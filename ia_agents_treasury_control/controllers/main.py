"""Controlador MCP — thin client para Odoo.sh y cualquier versión de Odoo.

Implementa el protocolo MCP 2024-11-05 (JSON-RPC 2.0 sobre HTTP) y delega
toda la lógica de negocio al servidor remoto de Uniasser en:
  https://apps.uniasser.net/agents/execute

La lógica crítica nunca reside en el módulo instalado.
Compatible con Odoo 16, 17, 18, 19 y Odoo.sh.
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
import urllib.request

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

_P = "ia_agents_treasury_control."
_AGENTS_EXECUTE = "https://apps.uniasser.net/agents/execute"

# Códigos de autorización OAuth en memoria (code → metadata). TTL 5 min.
_AUTH_CODES: dict[str, dict] = {}

# Mapa access_token → db_name. Se puebla en oauth_token; se pierde al reiniciar.
_TOKEN_DB: dict[str, str] = {}

# ── Definición de herramientas MCP ─────────────────────────────────────────────

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
                "date_from": {"type": "string", "description": "Fecha inicio YYYY-MM-DD."},
                "days_forecast": {"type": "integer", "default": 30},
            },
        },
    },
    {
        "name": "get_tax_status",
        "description": "Estado fiscal del trimestre: IVA repercutido, soportado y retenciones IRPF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quarter": {"type": "integer", "description": "Trimestre 1-4."},
                "year": {"type": "integer"},
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
                "message": {"type": "string", "description": "Texto con los datos (obligatorio)."},
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
            "SIEMPRE requiere aprobación humana."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_back": {"type": "integer", "default": 30},
                "confidence_threshold": {"type": "number", "default": 0.75},
            },
        },
    },
    {
        "name": "apply_reconciliation",
        "description": "Aplica matches de conciliación aprobados. REQUIERE aprobación explícita.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "matches": {"type": "array", "description": "Lista de matches a aplicar."},
            },
            "required": ["matches"],
        },
    },
    {
        "name": "process_email_invoices",
        "description": "Lee el buzón IMAP, extrae facturas PDF con OCR y crea borradores en Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "imap_host": {"type": "string", "default": "imap.gmail.com"},
                "imap_user": {"type": "string"},
                "imap_password": {"type": "string"},
                "imap_folder": {"type": "string", "default": "Facturas"},
            },
        },
    },
    {
        "name": "create_timesheet_entry",
        "description": "Registra un parte de horas en Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "task_name": {"type": "string"},
                "employee_email": {"type": "string"},
                "description": {"type": "string"},
                "hours": {"type": "number"},
                "date": {"type": "string", "description": "Fecha YYYY-MM-DD. Por defecto hoy."},
            },
            "required": ["project_name", "task_name", "employee_email", "description", "hours"],
        },
    },
    {
        "name": "create_timesheet_project",
        "description": "Crea un proyecto nuevo en Odoo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_timesheet_task",
        "description": "Crea una tarea nueva dentro de un proyecto existente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "task_name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["project_name", "task_name"],
        },
    },
    {
        "name": "get_alerts",
        "description": "Consolida alertas financieras: facturas vencidas, vencimientos fiscales, caja negativa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_forecast": {"type": "integer", "default": 30},
            },
        },
    },
    {
        "name": "get_account_ledger",
        "description": "Movimientos debe/haber de una cuenta contable. Busca por código o nombre.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_query": {"type": "string", "description": "Código (ej: 4300) o nombre."},
                "date_from": {"type": "string", "description": "Fecha inicio YYYY-MM-DD."},
                "date_to": {"type": "string"},
            },
            "required": ["account_query", "date_from"],
        },
    },
    {
        "name": "get_customer_pending_invoices",
        "description": "Facturas pendientes de cobro de un cliente.",
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


# ── Helpers ────────────────────────────────────────────────────────────────────

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
    import uuid as _uuid
    body = "event: message\ndata: " + json.dumps(data, ensure_ascii=False, default=str) + "\n\n"
    return Response(
        body,
        status=status,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "mcp-session-id": _uuid.uuid4().hex,
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
    """Devuelve (env, cursor_o_None). Funciona en cualquier versión de Odoo."""
    if request.env is not None:
        return request.env, None

    _bearer_token: str | None = None
    auth = request.httprequest.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        _bearer_token = auth[7:]

    try:
        import odoo.service.db as _db_service
        valid_dbs: list[str] = _db_service.list_dbs(True)
    except Exception:
        valid_dbs = []

    _candidates = [
        db_hint,
        getattr(request, "db", None),
        _bearer_token and _TOKEN_DB.get(_bearer_token),
    ]
    db: str | None = next(
        (c for c in _candidates if c and c in valid_dbs), None
    )

    if not db and _bearer_token:
        _param_key = f"{_P}mcp_secret_token"
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
                    _cr.execute(
                        "SELECT value FROM ir_config_parameter "
                        "WHERE key = %s LIMIT 1",
                        (f"{_P}license_key",),
                    )
                    lic_row = _cr.fetchone()
                    if lic_row and lic_row[0]:
                        db = candidate
                        break
            except Exception:
                continue

    if not db:
        return None, None

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


def _check_bearer(env) -> bool:
    if env is None:
        return False
    expected = _get_param(env, "mcp_secret_token", "")
    if not expected:
        return True  # Sin token configurado: acepta todo (durante setup)
    auth = request.httprequest.headers.get("Authorization", "")
    return auth == f"Bearer {expected}"


# ── Llamada al servidor remoto de Uniasser ─────────────────────────────────────

def _call_remote(env, operation: str, params: dict) -> str:
    """Envía la operación al servidor remoto de Uniasser y devuelve el resultado."""
    icp = env["ir.config_parameter"].sudo()

    license_key = icp.get_param(f"{_P}license_key", "")
    odoo_api_key = icp.get_param(f"{_P}odoo_api_key", "")
    odoo_login = icp.get_param(f"{_P}odoo_login", "admin")
    anthropic_api_key = icp.get_param(f"{_P}anthropic_api_key", "")
    claude_model = icp.get_param(f"{_P}claude_model", "claude-sonnet-4-6")
    odoo_url = icp.get_param("web.base.url", "").rstrip("/")
    odoo_db = env.cr.dbname

    if not license_key:
        return "❌ Licencia no configurada. Ve a Ajustes → IA Treasury Control → Licencia."

    if not odoo_api_key:
        return (
            "❌ Odoo API Key no configurada.\n"
            "Ve a Ajustes → IA Treasury Control → Odoo API Key.\n"
            "Para generar la clave: Ajustes → Usuarios → tu usuario → Claves de API → Nueva clave."
        )

    payload = json.dumps({
        "license_key": license_key,
        "operation": operation,
        "odoo_url": odoo_url,
        "odoo_db": odoo_db,
        "odoo_login": odoo_login,
        "odoo_api_key": odoo_api_key,
        "anthropic_api_key": anthropic_api_key,
        "claude_model": claude_model,
        "params": params,
    }).encode("utf-8")

    req = urllib.request.Request(
        _AGENTS_EXECUTE,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("result", str(data))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("detail", str(exc))
        except Exception:
            detail = str(exc)
        _logger.error("IATC remote error %s: %s", operation, detail)
        return f"❌ Error del servidor Uniasser ({exc.code}): {detail}"
    except Exception as exc:
        _logger.error("IATC remote connection error: %s", exc)
        return f"❌ No se pudo conectar con el servidor de Uniasser: {exc}"


# ── Controlador HTTP ───────────────────────────────────────────────────────────

class IATCMCPController(http.Controller):

    # ── OAuth: resource metadata (RFC 9728) ───────────────────────────────────

    @http.route("/.well-known/oauth-protected-resource", auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_protected_resource(self, **_kwargs):
        req = request.httprequest
        scheme = req.headers.get("X-Forwarded-Proto", req.scheme)
        host = req.headers.get("X-Forwarded-Host", req.host)
        base_url = f"{scheme}://{host}"
        return Response(
            json.dumps({
                "resource": f"{base_url}/mcp",
                "authorization_servers": [base_url],
                "bearer_methods_supported": ["header"],
                "resource_documentation": f"{base_url}/mcp",
            }),
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
        return Response(
            json.dumps({
                "issuer": base_url,
                "authorization_endpoint": f"{base_url}/authorize",
                "token_endpoint": f"{base_url}/mcp/oauth/token",
                "registration_endpoint": f"{base_url}/oauth/register",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code"],
                "code_challenge_methods_supported": ["S256"],
                "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
            }),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    # ── OAuth: authorization + token ──────────────────────────────────────────

    @http.route(["/mcp/oauth/authorize", "/authorize"], auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_authorize(self, **kwargs):
        redirect_uri = kwargs.get("redirect_uri", "")
        state = kwargs.get("state", "")
        code_challenge = kwargs.get("code_challenge", "")
        code_challenge_method = kwargs.get("code_challenge_method", "S256")
        client_id = kwargs.get("client_id", "")

        if not redirect_uri:
            return Response("redirect_uri requerido", status=400)

        now = time.time()
        expired = [k for k, v in _AUTH_CODES.items() if now - v["created"] > 300]
        for k in expired:
            _AUTH_CODES.pop(k, None)

        code = secrets.token_urlsafe(32)
        _AUTH_CODES[code] = {
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "client_id": client_id,
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

        if code_data.get("code_challenge"):
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
            if challenge != code_data["code_challenge"]:
                return _err("PKCE incorrecto")

        db_hint = code_data.get("client_id") or None
        env, _cr = _open_env(db_hint)
        try:
            mcp_token = _get_param(env, "mcp_secret_token", "")
            access_token = mcp_token if mcp_token else secrets.token_urlsafe(32)
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

    # ── OAuth: dynamic client registration (RFC 7591) ─────────────────────────

    @http.route("/oauth/register", auth="none", csrf=False,
                methods=["POST", "OPTIONS"], type="http", save_session=False)
    def oauth_register(self, **_kwargs):
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
        client_id = getattr(request, "db", None) or "odoo_db"
        return Response(
            json.dumps({
                "client_id": client_id,
                "client_id_issued_at": int(time.time()),
                "redirect_uris": body.get("redirect_uris", []),
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "registration_client_uri": f"{base_url}/oauth/register",
            }),
            status=201,
            headers={"Content-Type": "application/json", **_CORS},
        )

    # ── MCP endpoint ──────────────────────────────────────────────────────────

    @http.route("/mcp", auth="none", csrf=False,
                methods=["GET", "POST", "OPTIONS"], type="http", save_session=False)
    def mcp_endpoint(self, **_kwargs):
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)

        if request.httprequest.method == "GET":
            return _json_resp({
                "name": "ia_agents_treasury_control",
                "version": "1.0.0",
                "protocol": "MCP/2024-11-05",
                "status": "ok",
                "powered_by": "Uniasser (apps.uniasser.net)",
            })

        accept = request.httprequest.headers.get("Accept", "")
        use_sse = "text/event-stream" in accept

        env, _cr = _open_env()
        try:
            return self._mcp_handle(env, use_sse)
        finally:
            if _cr is not None:
                _cr.close()

    def _mcp_handle(self, env, use_sse: bool):
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

        if method == "initialize":
            return _mcp_resp(_rpc_ok(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "ia_agents_treasury_control",
                    "version": "1.0.0",
                },
            }), use_sse)

        if method.startswith("notifications/"):
            return _mcp_resp({"jsonrpc": "2.0", "id": req_id, "result": {}}, use_sse)

        if method == "ping":
            return _mcp_resp(_rpc_ok(req_id, {}), use_sse)

        if method == "tools/list":
            return _mcp_resp(_rpc_ok(req_id, {"tools": _TOOLS}), use_sse)

        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            # health_check: responde localmente sin llamar al servidor remoto
            if tool_name == "health_check":
                try:
                    db_name = env.cr.dbname if env else "desconocida"
                    company = env["res.company"].sudo().search([], limit=1).name if env else "?"
                    base_url = _get_param(env, "", "") or env["ir.config_parameter"].sudo().get_param("web.base.url", "?") if env else "?"
                    license_key = _get_param(env, "license_key", "")
                    has_api_key = bool(_get_param(env, "odoo_api_key", ""))
                except Exception:
                    db_name = company = base_url = "?"
                    license_key = ""
                    has_api_key = False

                status_msg = (
                    f"✅ IA Treasury Control (MCP) — operativo\n\n"
                    f"📦 Base de datos : {db_name}\n"
                    f"🏢 Empresa       : {company}\n"
                    f"🌐 URL Odoo      : {base_url}\n"
                    f"🔑 Licencia      : {'✅ Configurada' if license_key else '⚠️ Sin configurar'}\n"
                    f"🔐 Odoo API Key  : {'✅ Configurada' if has_api_key else '⚠️ Sin configurar'}\n"
                    f"☁️  Agentes       : https://apps.uniasser.net/agents"
                )
                return _mcp_resp(_rpc_ok(req_id, {
                    "content": [{"type": "text", "text": status_msg}],
                }), use_sse)

            # Todas las demás herramientas → llamada al servidor remoto
            result_text = _call_remote(env, tool_name, tool_args)

            return _mcp_resp(_rpc_ok(req_id, {
                "content": [{"type": "text", "text": result_text}],
            }), use_sse)

        return _mcp_resp(_rpc_error(req_id, -32601, f"Método no soportado: {method}"), use_sse)
