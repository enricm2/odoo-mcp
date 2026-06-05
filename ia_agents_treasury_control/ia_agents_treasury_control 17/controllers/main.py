"""Controlador MCP nativo para Odoo 18.

Implementa el protocolo MCP 2024-11-05 (JSON-RPC 2.0 sobre HTTP) directamente
como un controlador Odoo, sin depender del proceso FastMCP externo.

Rutas:
  POST /mcp          — protocolo MCP (Claude Desktop / claude-remote)
  POST /webhook/whatsapp — mensajes WhatsApp desde n8n
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import secrets
import time
import urllib.parse
import uuid

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

_P = "ia_agents_treasury_control."

# Códigos de autorización OAuth en memoria (code → metadata). TTL 5 min.
_AUTH_CODES: dict[str, dict] = {}

# Mapa access_token → db_name (se puebla en oauth_token; se pierde al reiniciar Odoo).
_TOKEN_DB: dict[str, str] = {}

# ── Definición de herramientas MCP ────────────────────────────────────────────

_TOOLS = [
    {
        "name": "get_treasury_report",
        "description": (
            "Genera informe de tesorería con cobros pendientes, pagos pendientes "
            "y previsión de caja. Úsalo cuando el usuario pregunte por tesorería, "
            "cobros, pagos, saldo o cash flow."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Fecha inicio YYYY-MM-DD. Sin valor: todo el histórico."},
                "days_forecast": {"type": "integer", "description": "Días de previsión de caja.", "default": 30},
                "output_format": {"type": "string", "enum": ["text", "pdf", "whatsapp"], "default": "text"},
                "whatsapp_to": {"type": "string", "description": "Número WhatsApp (solo si output_format=whatsapp)."},
            },
        },
    },
    {
        "name": "get_tax_status",
        "description": "Estado fiscal del trimestre: IVA repercutido, soportado y retenciones IRPF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quarter": {"type": "integer", "description": "Trimestre 1-4. Por defecto: trimestre actual."},
                "year": {"type": "integer", "description": "Año. Por defecto: año actual."},
            },
        },
    },
    {
        "name": "create_draft_invoice",
        "description": (
            "Crea una factura en BORRADOR en Odoo desde lenguaje natural. "
            "NUNCA confirma ni envía sin aprobación del usuario."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Texto con los datos de la factura (obligatorio)."},
                "partner_name": {"type": "string"},
                "amount": {"type": "number"},
                "description": {"type": "string"},
                "date": {"type": "string", "description": "Fecha YYYY-MM-DD."},
            },
            "required": ["message"],
        },
    },
    {
        "name": "run_bank_reconciliation",
        "description": (
            "Propone matches entre movimientos bancarios y facturas pendientes. "
            "SIEMPRE requiere aprobación humana. Usa apply_reconciliation para aplicar."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_back": {"type": "integer", "default": 30},
                "confidence_threshold": {"type": "number", "default": 0.75},
                "whatsapp_to": {"type": "string"},
            },
        },
    },
    {
        "name": "apply_reconciliation",
        "description": "Aplica los matches aprobados creando pagos en borrador. REQUIERE aprobación explícita.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposals_json": {"type": "string", "description": "JSON de proposals de run_bank_reconciliation."},
                "approved_indices": {"type": "array", "items": {"type": "integer"}, "description": "Índices (desde 1) a aplicar."},
            },
            "required": ["proposals_json", "approved_indices"],
        },
    },
    {
        "name": "process_email_invoices",
        "description": "Lee el buzón IMAP, extrae facturas PDF con OCR y crea borradores en Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_messages": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "create_timesheet_entry",
        "description": (
            "Registra un parte de horas en Odoo (account.analytic.line). "
            "Si proyecto o tarea son ambiguos devuelve lista para elegir."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "task_name": {"type": "string"},
                "user_email": {"type": "string", "description": "Email del usuario en Odoo."},
                "description": {"type": "string"},
                "hours": {"type": "number", "description": "Horas decimales. 1.5 = 1h 30min."},
                "entry_date": {"type": "string", "description": "Fecha YYYY-MM-DD. Por defecto hoy."},
                "project_id": {"type": "integer", "description": "ID exacto del proyecto (para resolver ambigüedad)."},
                "task_id": {"type": "integer", "description": "ID exacto de la tarea."},
                "partner_id": {"type": "integer", "description": "ID del partner/cliente en Odoo (opcional, sobreescribe la resolución automática)."},
                "account_id": {"type": "integer", "description": "ID de la cuenta analítica en Odoo (opcional, sobreescribe la resolución automática)."},
            },
            "required": ["project_name", "task_name", "user_email", "description", "hours"],
        },
    },
    {
        "name": "create_timesheet_project",
        "description": "Crea un proyecto nuevo en Odoo, opcionalmente vinculado a un partner.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "partner_name": {"type": "string"},
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "create_timesheet_task",
        "description": "Crea una tarea nueva dentro de un proyecto existente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_name": {"type": "string"},
                "project_id": {"type": "integer"},
                "project_name": {"type": "string", "default": ""},
            },
            "required": ["task_name", "project_id"],
        },
    },
    {
        "name": "get_alerts",
        "description": "Consolida alertas financieras: facturas vencidas, vencimientos fiscales, caja negativa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "whatsapp_to": {"type": "string"},
                "forecast_days": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_account_ledger",
        "description": "Movimientos debe/haber de una cuenta contable. Busca por código o nombre.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_query": {"type": "string", "description": "Código (ej: 4300) o nombre (ej: Clientes)."},
                "date_from": {"type": "string", "description": "Fecha inicio YYYY-MM-DD."},
                "date_to": {"type": "string"},
                "account_id": {"type": "integer", "description": "ID exacto (para resolver ambigüedad)."},
            },
            "required": ["account_query", "date_from"],
        },
    },
    {
        "name": "get_customer_pending_invoices",
        "description": "Facturas pendientes de cobro de un cliente. Las rectificativas no aparecen.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "partner_name": {"type": "string"},
            },
            "required": ["partner_name"],
        },
    },
    {
        "name": "get_bank_account_balances",
        "description": "Saldos de todas las cuentas bancarias del grupo 572.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_bank_account_statement",
        "description": "Extracto bancario con saldo arrastrado desde una fecha.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_query": {"type": "string", "description": "Nombre del banco o código 572x."},
                "date_from": {"type": "string"},
                "account_id": {"type": "integer"},
            },
            "required": ["account_query", "date_from"],
        },
    },
    {
        "name": "health_check",
        "description": "Comprueba que el servidor MCP y la conexión con Odoo están operativos.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, mcp-session-id",
    "Access-Control-Expose-Headers": "mcp-session-id",
}


def _json_resp(data: dict, status: int = 200) -> Response:
    return Response(
        json.dumps(data, ensure_ascii=False, default=str),
        status=status,
        headers={"Content-Type": "application/json; charset=utf-8", **_CORS},
    )


def _sse_resp(data: dict, status: int = 200) -> Response:
    """Streamable HTTP MCP transport — formato SSE que espera Claude Desktop."""
    body = "event: message\ndata: " + json.dumps(data, ensure_ascii=False, default=str) + "\n\n"
    session_id = uuid.uuid4().hex
    return Response(
        body,
        status=status,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "mcp-session-id": session_id,
            **_CORS,
        },
    )


def _mcp_resp(data: dict, use_sse: bool, status: int = 200) -> Response:
    return _sse_resp(data, status) if use_sse else _json_resp(data, status)


def _rpc_ok(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _rpc_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _get_param(env, key: str, default: str = "") -> str:
    if env is None:
        return default
    return env["ir.config_parameter"].sudo().get_param(f"{_P}{key}", default)


def _open_env(db_hint: str | None = None):
    """Devuelve (env, cursor_o_None) abriendo cursor propio si request.env es None.

    Orden de resolución:
      1. request.env  (contexto normal con DB ya abierta)
      2. db_hint      — solo si coincide con una BD real en la lista de BDs válidas
      3. request.db   (Odoo lo rellena cuando hay sesión activa)
      4. _TOKEN_DB    (mapa en memoria token→db_name, poblado tras OAuth)
      5. Escaneo de BDs: la primera con nuestro módulo instalado
    El cursor devuelto DEBE cerrarse en finally por el llamador.
    """
    if request.env is not None:
        return request.env, None

    # Extraer Bearer token para lookup en caché y para cachear el resultado
    _bearer_token: str | None = None
    auth = request.httprequest.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        _bearer_token = auth[7:]

    # Obtener lista de BDs válidas (usada para validar candidatos y para el escaneo)
    try:
        import odoo.service.db as _db_service
        valid_dbs: list[str] = _db_service.list_dbs(True)
    except Exception:
        valid_dbs = []

    # Candidatos ordenados por prioridad — filtramos contra BDs válidas
    _candidates = [
        db_hint,
        getattr(request, "db", None),
        _bearer_token and _TOKEN_DB.get(_bearer_token),
    ]
    db: str | None = next(
        (c for c in _candidates if c and c in valid_dbs),
        None,
    )

    if not db and _bearer_token:
        # Buscar la BD cuyo mcp_secret_token coincide con el Bearer token.
        # Esto resuelve el problema post-reinicio cuando _TOKEN_DB está vacío:
        # el Bearer token ES el mcp_secret_token almacenado en ir.config_parameter.
        _param_key = "ia_agents_treasury_control.mcp_secret_token"
        for candidate in valid_dbs:
            try:
                from odoo.modules.registry import Registry as _Reg
                with _Reg(candidate).cursor() as _cr:
                    _cr.execute(
                        "SELECT value FROM ir_config_parameter WHERE key = %s LIMIT 1",
                        (_param_key,),
                    )
                    row = _cr.fetchone()
                    if row and row[0] == _bearer_token:
                        db = candidate
                        break
            except Exception:
                continue

    if not db:
        # Escanear: primera BD con el módulo instalado y licencia activa
        for candidate in valid_dbs:
            try:
                from odoo.modules.registry import Registry as _Reg
                with _Reg(candidate).cursor() as _cr:
                    _cr.execute(
                        "SELECT 1 FROM ir_module_module "
                        "WHERE name='ia_agents_treasury_control' AND state='installed'"
                    )
                    if not _cr.fetchone():
                        continue
                    # Preferir BDs con licencia configurada
                    _cr.execute(
                        "SELECT value FROM ir_config_parameter "
                        "WHERE key = 'ia_agents_treasury_control.license_key' LIMIT 1"
                    )
                    lic_row = _cr.fetchone()
                    if lic_row and lic_row[0]:
                        db = candidate
                        break
            except Exception:
                continue

    if not db:
        return None, None

    # Cachear para evitar el escaneo en peticiones futuras
    if _bearer_token:
        _TOKEN_DB[_bearer_token] = db

    try:
        from odoo.modules.registry import Registry
        import odoo.api
        cr = Registry(db).cursor()
        env = odoo.api.Environment(cr, 1, {})
        return env, cr
    except Exception:
        return None, None


def _run_async(coro):
    """Ejecuta una corrutina de forma segura desde un hilo síncrono (compatible con gevent)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Gevent / Odoo multithread: crear un loop nuevo en un thread separado
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
    except RuntimeError:
        pass
    return asyncio.run(coro)


def _check_bearer(env) -> bool:
    """Verifica el token Bearer de la cabecera Authorization."""
    if env is None:
        # Sin BD no podemos validar el token → denegar
        return False
    expected = _get_param(env, "mcp_secret_token", "")
    if not expected:
        return True  # Sin token configurado, acepta todo (modo desarrollo)
    auth = request.httprequest.headers.get("Authorization", "")
    return auth == f"Bearer {expected}"


# ── Dispatcher de herramientas MCP ────────────────────────────────────────────

def _msg(result: dict) -> str:
    """Extrae el texto de respuesta de cualquier dict de agente.

    Los agentes devuelven dicts con clave 'message', 'report' o 'error'.
    Usar siempre este helper en lugar de result["message"] para evitar
    KeyError cuando el agente retorna un error sin clave 'message'.
    """
    return (
        result.get("message")
        or result.get("report")
        or result.get("error")
        or repr(result)
    )


async def _dispatch_tool(tool_name: str, args: dict, env) -> str:
    """Ejecuta la herramienta solicitada y devuelve el texto resultante."""
    from ..odoo_env_client import OdooEnvClient
    from ..agents import (
        run_treasury_agent, run_tax_agent, run_invoice_agent,
        run_email_invoice_agent, run_reconciliation_agent, apply_approved_matches,
        run_alert_agent, run_timesheet_agent, create_odoo_project, create_odoo_task,
        get_account_movements, get_pending_customer_invoices,
        get_bank_balances, get_bank_statement,
    )
    from ..services.llm_service import LLMService
    from ..services.bank_service import BankService
    from ..services.email_service import EmailService
    from ..services.ocr_service import OCRService

    odoo = OdooEnvClient(env)
    llm = LLMService(env)

    if tool_name == "get_treasury_report":
        result = await run_treasury_agent(
            odoo=odoo, llm=llm,
            days_forecast=args.get("days_forecast", 30),
            date_from=args.get("date_from"),
        )
        report = _msg(result)
        if args.get("output_format") == "whatsapp" or args.get("whatsapp_to"):
            from ..services.whatsapp_sender import send_whatsapp
            to = args.get("whatsapp_to") or ""
            ok = await asyncio.to_thread(send_whatsapp, env, to, report)
            suffix = "\n\n✅ Informe enviado por WhatsApp." if ok else "\n\n⚠️ El informe no pudo enviarse por WhatsApp (revisa la configuración en Ajustes)."
            return report + suffix
        return report

    if tool_name == "get_tax_status":
        result = await run_tax_agent(
            odoo=odoo, llm=llm,
            quarter=args.get("quarter"),
            year=args.get("year"),
        )
        report = _msg(result)
        if result.get("data", {}).get("alert"):
            return f"⚠️ ALERTA FISCAL — Variación superior al 15%\n\n{report}"
        return report

    if tool_name == "create_draft_invoice":
        result = await run_invoice_agent(
            odoo=odoo, llm=llm,
            message=args["message"],
            partner_name=args.get("partner_name"),
            amount=args.get("amount"),
            description=args.get("description"),
            invoice_date=args.get("date"),
        )
        return _msg(result)

    if tool_name == "run_bank_reconciliation":
        bank = BankService(env)
        result = await run_reconciliation_agent(
            odoo=odoo, bank_service=bank,
            days_back=args.get("days_back", 30),
            confidence_threshold=args.get("confidence_threshold", 0.75),
        )
        proposals_json = json.dumps(result.get("proposals", []), default=str)
        return f"{_msg(result)}\n\n[proposals_json]:\n{proposals_json}"

    if tool_name == "apply_reconciliation":
        proposals = json.loads(args["proposals_json"])
        result = await apply_approved_matches(
            odoo=odoo,
            proposals=proposals,
            approved_indices=args["approved_indices"],
        )
        details = []
        for c in result.get("created", []):
            url = f"{odoo.url}/web#id={c['payment_id']}&model=account.payment&view_type=form"
            details.append(f"  ✓ {c['partner']} €{c['amount']:.2f} → #{c['payment_id']} [{url}]")
        for e in result.get("errors", []):
            details.append(f"  ✗ Índice {e.get('index', '?')}: {e.get('error', '')}")
        return _msg(result) + ("\n\nDetalle:\n" + "\n".join(details) if details else "")

    if tool_name == "process_email_invoices":
        email_svc = EmailService(env)
        ocr_svc = OCRService(llm)
        result = await run_email_invoice_agent(
            odoo=odoo, email_svc=email_svc, ocr_svc=ocr_svc,
            max_messages=args.get("max_messages", 20),
        )
        details = [
            f"  {'✓' if r.get('success') else '✗'} {r.get('filename', '?')}: "
            f"{r.get('partner', r.get('error', ''))}"
            for r in result.get("results", [])
        ]
        return _msg(result) + ("\n\n" + "\n".join(details) if details else "")

    if tool_name == "create_timesheet_entry":
        result = await run_timesheet_agent(
            odoo=odoo,
            project_name=args["project_name"],
            task_name=args["task_name"],
            user_email=args["user_email"],
            description=args["description"],
            hours=float(args["hours"]),
            entry_date=args.get("entry_date"),
            project_id=args.get("project_id"),
            task_id=args.get("task_id"),
            partner_id=args.get("partner_id"),
            account_id=args.get("account_id"),
        )
        return _msg(result)

    if tool_name == "create_timesheet_project":
        result = await create_odoo_project(odoo, args["project_name"], args.get("partner_name"))
        return _msg(result)

    if tool_name == "create_timesheet_task":
        result = await create_odoo_task(
            odoo, args["task_name"], args["project_id"], args.get("project_name", "")
        )
        return _msg(result)

    if tool_name == "get_alerts":
        forecast_days = args.get("forecast_days") or int(_get_param(env, "forecast_days", "30"))
        result = await run_alert_agent(odoo=odoo, forecast_days=forecast_days)
        return _msg(result)

    if tool_name == "get_account_ledger":
        result = await get_account_movements(
            odoo, args["account_query"], args["date_from"],
            args.get("date_to"), args.get("account_id"),
        )
        return _msg(result)

    if tool_name == "get_customer_pending_invoices":
        result = await get_pending_customer_invoices(odoo, args["partner_name"])
        return _msg(result)

    if tool_name == "get_bank_account_balances":
        result = await get_bank_balances(odoo)
        return _msg(result)

    if tool_name == "get_bank_account_statement":
        result = await get_bank_statement(
            odoo, args["account_query"], args["date_from"], args.get("account_id")
        )
        return _msg(result)

    return f"Herramienta desconocida: {tool_name}"


# ── Controlador HTTP ──────────────────────────────────────────────────────────

class IATCMCPController(http.Controller):

    # ── OAuth 2.0 resource metadata (RFC 9728) — requerido por claude.ai ─────

    @http.route("/.well-known/oauth-protected-resource", auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_protected_resource(self, **_kwargs):
        req = request.httprequest
        scheme = req.headers.get("X-Forwarded-Proto", req.scheme)
        host = req.headers.get("X-Forwarded-Host", req.host)
        base_url = f"{scheme}://{host}"
        metadata = {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [base_url],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{base_url}/mcp",
        }
        return Response(
            json.dumps(metadata),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    @http.route("/.well-known/oauth-authorization-server", auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_authorization_server_metadata(self, **_kwargs):
        req = request.httprequest
        scheme = req.headers.get("X-Forwarded-Proto", req.scheme)
        host = req.headers.get("X-Forwarded-Host", req.host)
        base_url = f"{scheme}://{host}"
        metadata = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/mcp/oauth/token",
            "registration_endpoint": f"{base_url}/oauth/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        }
        return Response(
            json.dumps(metadata),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    @http.route(["/mcp/oauth/authorize", "/authorize"], auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_authorize(self, **kwargs):
        """Authorization Code + PKCE — redirige inmediatamente (servidor personal, sin pantalla de login)."""
        redirect_uri = kwargs.get("redirect_uri", "")
        state = kwargs.get("state", "")
        code_challenge = kwargs.get("code_challenge", "")
        code_challenge_method = kwargs.get("code_challenge_method", "S256")
        # client_id = nombre de BD (lo ponemos en iatc_mcp_oauth_client_id)
        client_id = kwargs.get("client_id", "")

        if not redirect_uri:
            return Response("redirect_uri requerido", status=400)

        # Limpiar códigos caducados (> 5 min)
        now = time.time()
        expired = [k for k, v in _AUTH_CODES.items() if now - v["created"] > 300]
        for k in expired:
            _AUTH_CODES.pop(k, None)

        code = secrets.token_urlsafe(32)
        _AUTH_CODES[code] = {
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "client_id": client_id,  # nombre de BD para abrir cursor en oauth_token
            "created": now,
        }

        sep = "&" if "?" in redirect_uri else "?"
        location = redirect_uri + sep + urllib.parse.urlencode({"code": code, "state": state})
        return Response(status=302, headers={"Location": location})

    @http.route("/mcp/oauth/token", auth="none", csrf=False,
                methods=["POST", "OPTIONS"], type="http", save_session=False)
    def oauth_token(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)

        """Intercambia authorization_code por access_token."""
        grant_type = kwargs.get("grant_type", "")
        code = kwargs.get("code", "")
        code_verifier = kwargs.get("code_verifier", "")

        def _err(msg, status=400):
            return Response(
                json.dumps({"error": "invalid_grant", "error_description": msg}),
                status=status,
                headers={"Content-Type": "application/json"},
            )

        if grant_type != "authorization_code":
            return _err("grant_type debe ser authorization_code")

        code_data = _AUTH_CODES.pop(code, None)
        if not code_data:
            return _err("Código inválido o caducado")

        # Validar PKCE S256
        if code_data.get("code_challenge"):
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
            if challenge != code_data["code_challenge"]:
                return _err("PKCE incorrecto")

        # El flujo PKCE (que usa claude.ai) NO envía client_secret —
        # la seguridad viene del code_verifier ya validado arriba.
        # El access_token que devolvemos ES el mcp_secret_token almacenado en Odoo,
        # de modo que Claude lo usará como Bearer en las llamadas a /mcp.
        db_hint = code_data.get("client_id") or None
        env, _cr = _open_env(db_hint)
        try:
            # mcp_secret_token es el Bearer que protege el endpoint /mcp
            mcp_token = _get_param(env, "mcp_secret_token", "")
            access_token = mcp_token if mcp_token else secrets.token_urlsafe(32)

            # Cachear access_token → db para resolución rápida en /mcp
            if access_token and env is not None:
                try:
                    _TOKEN_DB[access_token] = env.cr.dbname
                except Exception:
                    pass
        finally:
            if _cr is not None:
                _cr.close()

        return Response(
            json.dumps({
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 86400 * 30,
            }),
            status=200,
            headers={"Content-Type": "application/json", **_CORS},
        )

    # ── OAuth Dynamic Client Registration (RFC 7591) ─────────────────────────

    @http.route("/oauth/register", auth="none", csrf=False,
                methods=["POST", "OPTIONS"], type="http", save_session=False)
    def oauth_register(self, **_kwargs):
        """Registro dinámico de cliente OAuth (RFC 7591).
        Servidor personal: acepta cualquier cliente y devuelve un client_id estático.
        """
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)
        try:
            body = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except (ValueError, json.JSONDecodeError):
            body = {}
        req = request.httprequest
        scheme = req.headers.get("X-Forwarded-Proto", req.scheme)
        host = req.headers.get("X-Forwarded-Host", req.host)
        base_url = f"{scheme}://{host}"
        client_id = "odoo18_db"
        redirect_uris = body.get("redirect_uris", [])
        response = {
            "client_id": client_id,
            "client_id_issued_at": int(time.time()),
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "registration_client_uri": f"{base_url}/oauth/register",
        }
        return Response(
            json.dumps(response),
            status=201,
            headers={"Content-Type": "application/json", **_CORS},
        )

    # ── MCP endpoint ──────────────────────────────────────────────────────────

    @http.route("/mcp", auth="none", csrf=False, methods=["GET", "POST", "OPTIONS"], type="http", save_session=False)
    def mcp_endpoint(self, **_kwargs):
        # OPTIONS → preflight CORS
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)

        # GET → información básica del servidor (no necesita BD)
        if request.httprequest.method == "GET":
            return _json_resp({
                "name": "ia_agents_treasury_control",
                "version": "18.0.1.0.0",
                "protocol": "MCP/2024-11-05",
                "status": "ok",
            })

        # Detect Streamable HTTP transport (Claude Desktop sends Accept: text/event-stream)
        accept = request.httprequest.headers.get("Accept", "")
        use_sse = "text/event-stream" in accept

        # Abrir entorno de BD (en server_wide_modules context request.env puede ser None)
        env, _cr = _open_env()
        try:
            return self._mcp_handle(env, use_sse)
        finally:
            if _cr is not None:
                _cr.close()

    def _mcp_handle(self, env, use_sse: bool):
        """Procesamiento MCP con entorno BD ya abierto."""
        # Verificar Bearer token
        if not _check_bearer(env):
            resp = _mcp_resp(
                {"error": "Unauthorized — Bearer token incorrecto"},
                use_sse, status=401,
            )
            resp.headers["WWW-Authenticate"] = 'Bearer realm="IA Treasury Control MCP"'
            return resp

        try:
            body = request.httprequest.get_data(as_text=True)
            rpc = json.loads(body)
        except (ValueError, json.JSONDecodeError) as exc:
            return _mcp_resp(_rpc_error(None, -32700, f"JSON inválido: {exc}"), use_sse)

        req_id = rpc.get("id")
        method = rpc.get("method", "")
        params = rpc.get("params", {})

        # ── initialize ────────────────────────────────────────────────────────
        if method == "initialize":
            return _mcp_resp(_rpc_ok(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "ia_agents_treasury_control",
                    "version": "18.0.1.0.0",
                },
            }), use_sse)

        # ── notifications (no response needed) ───────────────────────────────
        if method.startswith("notifications/"):
            return _mcp_resp({"jsonrpc": "2.0", "id": req_id, "result": {}}, use_sse)

        # ── ping ─────────────────────────────────────────────────────────────
        if method == "ping":
            return _mcp_resp(_rpc_ok(req_id, {}), use_sse)

        # ── tools/list ────────────────────────────────────────────────────────
        if method == "tools/list":
            return _mcp_resp(_rpc_ok(req_id, {"tools": _TOOLS}), use_sse)

        # ── tools/call ────────────────────────────────────────────────────────
        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            # health_check siempre funciona (diagnóstico sin licencia)
            if tool_name == "health_check":
                dev_mode = _get_param(env, "dev_mode", "0") in ("1", "true", "True")
                license_key = _get_param(env, "license_key", "")
                if dev_mode:
                    lic_info = "MODO DESARROLLO (licencia no verificada)"
                elif not license_key:
                    lic_info = "⚠️ Licencia no configurada"
                else:
                    customer = _get_param(env, "license_customer", "")
                    expires  = _get_param(env, "license_expires", "")
                    lic_info = f"Licencia válida — {customer} (hasta {expires})"

                # Datos de conexión
                try:
                    db_name  = env.cr.dbname if env else "desconocida"
                    company  = env["res.company"].sudo().search([], limit=1).name if env else "?"
                    odoo_url = _get_param(env, "", "").replace(_P, "") or "https://odoo.uniasser.net"
                    base_url = env["ir.config_parameter"].sudo().get_param("web.base.url", "?") if env else "?"
                except Exception:
                    db_name = company = base_url = "?"

                status_msg = (
                    f"✅ IA Agents Treasury Control — operativo\n\n"
                    f"📦 Base de datos : {db_name}\n"
                    f"🏢 Empresa       : {company}\n"
                    f"🌐 URL Odoo      : {base_url}\n"
                    f"🔑 Licencia      : {lic_info}"
                )
                return _mcp_resp(_rpc_ok(req_id, {
                    "content": [{"type": "text", "text": status_msg}],
                }), use_sse)

            # Verificar licencia antes de ejecutar cualquier otra herramienta.
            # En modo desarrollo (iatc_dev_mode=1) se omite la comprobación.
            dev_mode = _get_param(env, "dev_mode", "0") in ("1", "true", "True")
            if not dev_mode:
                from ..models.license_manager import require_license
                license_error = require_license(env)
                if license_error:
                    return _mcp_resp(_rpc_ok(req_id, {
                        "content": [{"type": "text", "text": license_error}],
                        "isError": True,
                    }), use_sse)

            try:
                result_text = _run_async(
                    _dispatch_tool(tool_name, tool_args, env)
                )
            except Exception as exc:
                _logger.exception("MCP tool unhandled error: %s", exc)
                result_text = f"Error al ejecutar {tool_name}: {exc}"

            return _mcp_resp(_rpc_ok(req_id, {
                "content": [{"type": "text", "text": result_text}],
            }), use_sse)

        # Método no reconocido
        return _mcp_resp(_rpc_error(req_id, -32601, f"Método no soportado: {method}"), use_sse)

    # ── Webhook WhatsApp ──────────────────────────────────────────────────────

    @http.route("/webhook/whatsapp", auth="none", csrf=False, methods=["POST"], type="http", save_session=False)
    def whatsapp_webhook(self, **_kwargs):
        try:
            payload = json.loads(request.httprequest.get_data(as_text=True))
        except (ValueError, json.JSONDecodeError):
            return _json_resp({"error": "JSON inválido"}, status=400)

        from_number = payload.get("from", "").strip()
        body = payload.get("body", "").strip()

        if not from_number or not body:
            return _json_resp({"error": "Faltan campos 'from' o 'body'"}, status=400)

        env, _cr = _open_env()
        try:
            # Verificar licencia también en el webhook
            from ..models.license_manager import require_license
            license_error = require_license(env)
            if license_error:
                return _json_resp({"status": "ok", "response_text": license_error})

            from ..odoo_env_client import OdooEnvClient
            from ..services.llm_service import LLMService
            from ..services.bank_service import BankService
            from ..services.webhook_handler import dispatch

            odoo = OdooEnvClient(env)
            llm = LLMService(env)
            bank = BankService(env)

            try:
                response_text = _run_async(
                    dispatch(message=body, from_number=from_number, odoo=odoo, llm=llm, bank=bank)
                )
            except Exception as exc:
                _logger.exception("Webhook WhatsApp error: %s", exc)
                response_text = "Ha ocurrido un error interno. Por favor, inténtalo de nuevo."
        finally:
            if _cr is not None:
                _cr.close()

        _logger.info("webhook.dispatch_ok from=%s len=%d", from_number, len(response_text))
        return _json_resp({"status": "ok", "from": from_number, "response_text": response_text})
