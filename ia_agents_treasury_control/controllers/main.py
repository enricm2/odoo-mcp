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
        "description": "Movimientos debe/haber de una cuenta contable. Busca por código o nombre. "
        "Usa prefijos del PGC español: 43=clientes, 44=deudores, 40=proveedores, 41=acreedores, "
        "572=bancos, 700=ventas, 600=compras, 170=Capex, etc. "
        "Agregación automática: un prefijo numérico puro (ej: '43', '700', '600') agrega automáticamente "
        "todas las subcuentas en una sola llamada, sin pedir aclaración. "
        "Con group_by_month=True, desglosa el flujo mensual. "
        "Con exclude_self_offsetting=True, excluye apuntes auto-compensantes (Debe=Haber, misma fecha, misma cuenta).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_query": {"type": "string", "description": "Código (ej: 4300) o prefijo numérico (ej: '43' agrega todas las 43xx)."},
                "date_from": {"type": "string", "description": "Fecha inicio YYYY-MM-DD."},
                "date_to": {"type": "string"},
                "aggregate_by_prefix": {"type": "boolean", "description": "Si True, suma todas las cuentas que empiecen por el prefijo (automático para prefijos numéricos)."},
                "group_by_month": {"type": "boolean", "description": "Si True, agrupa los resultados por mes."},
                "exclude_self_offsetting": {"type": "boolean", "description": "Si True, excluye apuntes auto-compensantes (Debe=Haber, misma fecha, misma cuenta)."},
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
        "name": "get_treasury_forecast",
        "description": (
            "Previsión de tesorería a 30, 60 y 90 días. Combina las facturas pendientes "
            "de cobro y pago con el ritmo histórico de ventas y compras de los últimos "
            "6 meses para proyectar el saldo de caja en cada horizonte. Úsalo cuando "
            "el usuario pregunte por previsión, forecast, liquidez futura o cash flow "
            "a medio plazo."
        ),
        "inputSchema": {"type": "object", "properties": {}},
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


def _get_base_url_from_request() -> str:
    """Obtiene la URL base desde los headers HTTP del request actual.

    Garantiza que cada instancia de Odoo devuelva su propia URL correcta,
    independientemente de qué base de datos seleccione _open_env() en un
    entorno multi-tenant. Los proxies inversos propagan X-Forwarded-Proto
    y X-Forwarded-Host, por lo que este valor es siempre fiable.
    """
    req = request.httprequest
    scheme = req.headers.get("X-Forwarded-Proto", req.scheme)
    host = req.headers.get("X-Forwarded-Host", req.host)
    return f"{scheme}://{host}".rstrip("/")


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
    auth = request.httprequest.headers.get("Authorization", "")
    _logger.info("IATC MCP: Checking bearer token - expected configured: %s, received auth header: %s", bool(expected), bool(auth))
    
    # TEMPORAL: Aceptar cualquier token para depuración
    if not expected:
        _logger.info("IATC MCP: No token configured - accepting request")
        return True  # Sin token configurado: acepta todo (durante setup)
    
    if not auth:
        _logger.warning("IATC MCP: No Authorization header provided")
        return False
    
    # TEMPORAL: Aceptar cualquier token que tenga el formato Bearer
    if auth.startswith("Bearer "):
        token = auth[7:]
        _logger.info("IATC MCP: Accepting Bearer token (temporal debug mode): %s...", token[:10])
        return True
    
    # Check if the token matches the configured token OR if it's in the _TOKEN_DB map
    if auth == f"Bearer {expected}":
        _logger.info("IATC MCP: Bearer token matches configured token")
        return True
    
    # Also check if the token is a valid OAuth access token
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if token in _TOKEN_DB:
        _logger.info("IATC MCP: Bearer token found in _TOKEN_DB map")
        return True
    
    _logger.warning("IATC MCP: Bearer token mismatch - expected Bearer %s..., got %s...", expected[:10] if expected else "None", token[:10] if token else "None")
    return False


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

    # Si no hay API key de Anthropic, usar free trial (enviar null para indicar uso de trial)
    anthropic_key_to_send = anthropic_api_key if anthropic_api_key else None

    payload = json.dumps({
        "license_key": license_key,
        "operation": operation,
        "odoo_url": odoo_url,
        "odoo_db": odoo_db,
        "odoo_login": odoo_login,
        "odoo_api_key": odoo_api_key,
        "anthropic_api_key": anthropic_key_to_send,
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
        _logger.info("IATC OAuth: /.well-known/oauth-protected-resource called")
        # La URL base se extrae SIEMPRE del request HTTP, no de web.base.url de la BD.
        # En entornos multi-tenant, _open_env() podría seleccionar la BD de otro cliente
        # y devolver su web.base.url, que sería una URL incorrecta para esta instancia.
        base_url = _get_base_url_from_request()
        _logger.info("IATC OAuth: base_url from request: %s", base_url)
        response_data = {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [base_url],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{base_url}/mcp",
        }
        _logger.info("IATC OAuth: Returning protected resource metadata: %s", response_data)
        return Response(
            json.dumps(response_data),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    @http.route("/.well-known/oauth-authorization-server", auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_authorization_server_metadata(self, **_kwargs):
        _logger.info("IATC OAuth: /.well-known/oauth-authorization-server called")
        base_url = _get_base_url_from_request()
        _logger.info("IATC OAuth: base_url from request: %s", base_url)
        response_data = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/mcp/oauth/token",
            "registration_endpoint": f"{base_url}/oauth/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        }
        _logger.info("IATC OAuth: Returning authorization server metadata: %s", response_data)
        return Response(
            json.dumps(response_data),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    # ── OAuth: authorization + token ──────────────────────────────────────────

    @http.route(["/mcp/oauth/authorize", "/authorize"], auth="none", csrf=False,
                methods=["GET"], type="http", save_session=False)
    def oauth_authorize(self, **kwargs):
        _logger.info("IATC OAuth: /authorize called with kwargs: %s", kwargs)
        redirect_uri = kwargs.get("redirect_uri", "")
        state = kwargs.get("state", "")
        code_challenge = kwargs.get("code_challenge", "")
        code_challenge_method = kwargs.get("code_challenge_method", "S256")
        client_id = kwargs.get("client_id", "")

        _logger.info("IATC OAuth authorize: redirect_uri=%s client_id=%s", redirect_uri, client_id)

        if not redirect_uri:
            _logger.error("IATC OAuth authorize: Missing redirect_uri")
            return Response("redirect_uri requerido", status=400)

        # Usar base de datos configurada en el módulo como prioridad para validar client_id
        env, _cr = _open_env()
        configured_db = None
        try:
            configured_db = env["ir.config_parameter"].sudo().get_param(f"{_P}mcp_database", "") if env else ""
            _logger.info("IATC OAuth authorize: configured_db from module config: %s", configured_db)
        except Exception:
            pass
        finally:
            if _cr is not None:
                _cr.close()

        # No validar estrictamente client_id - permitir cualquier client_id válido
        # La validación real se hace en el endpoint de token usando la base de datos correcta
        if configured_db and client_id and client_id != configured_db:
            _logger.info("IATC OAuth authorize: client_id differs from configured_db (client_id=%s, configured=%s) - allowing anyway", client_id, configured_db)

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
        _logger.info("IATC OAuth authorize: Generated auth code, redirecting to: %s", redirect_uri)

        sep = "&" if "?" in redirect_uri else "?"
        location = redirect_uri + sep + urllib.parse.urlencode({"code": code, "state": state})
        return Response(status=302, headers={"Location": location})

    @http.route("/mcp/oauth/token", auth="none", csrf=False,
                methods=["POST", "OPTIONS"], type="http", save_session=False)
    def oauth_token(self, **kwargs):
        _logger.info("IATC OAuth: /mcp/oauth/token called")
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)

        grant_type = kwargs.get("grant_type", "")
        code = kwargs.get("code", "")
        code_verifier = kwargs.get("code_verifier", "")

        _logger.info("IATC OAuth token: grant_type=%s code=%s", grant_type, code[:10] if code else "None")

        def _err(msg, status=400):
            _logger.error("IATC OAuth token error: %s", msg)
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

        _logger.info("IATC OAuth token: Code data found for client_id=%s", code_data.get("client_id"))

        if code_data.get("code_challenge"):
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
            if challenge != code_data["code_challenge"]:
                return _err("PKCE incorrecto")

        # Usar base de datos configurada en el módulo como prioridad
        env, _cr = _open_env()
        configured_db = None
        try:
            configured_db = env["ir.config_parameter"].sudo().get_param(f"{_P}mcp_database", "") if env else ""
            _logger.info("IATC OAuth token: configured_db from module config: %s", configured_db)
        except Exception:
            pass
        finally:
            if _cr is not None:
                _cr.close()

        # Usar base de datos configurada o client_id como fallback
        db_hint = configured_db or code_data.get("client_id") or None
        _logger.info("IATC OAuth token: Using db_hint=%s", db_hint)
        
        env, _cr = _open_env(db_hint)
        try:
            mcp_token = _get_param(env, "mcp_secret_token", "")
            _logger.info("IATC OAuth token: MCP token configured: %s", bool(mcp_token))
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
        _logger.info("IATC OAuth: /oauth/register called")
        if request.httprequest.method == "OPTIONS":
            return Response(status=204, headers=_CORS)
        try:
            body = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except (ValueError, json.JSONDecodeError):
            body = {}
        _logger.info("IATC OAuth register: Request body: %s", body)

        # base_url siempre desde los headers HTTP (URL correcta por instancia)
        base_url = _get_base_url_from_request()
        _logger.info("IATC OAuth register: base_url from request: %s", base_url)

        # client_id: usar mcp_database configurado en la BD o el nombre de BD actual
        env, _cr = _open_env()
        try:
            configured_db = env["ir.config_parameter"].sudo().get_param(f"{_P}mcp_database", "") if env else ""
            client_id = configured_db or getattr(request, "db", None) or (env.cr.dbname if env else None) or "odoo_db"
            _logger.info("IATC OAuth register: client_id=%s", client_id)
        except Exception:
            client_id = getattr(request, "db", None) or "odoo_db"
        finally:
            if _cr is not None:
                _cr.close()

        response_data = {
            "client_id": client_id,
            "client_id_issued_at": int(time.time()),
            "redirect_uris": body.get("redirect_uris", []),
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "registration_client_uri": f"{base_url}/oauth/register",
        }
        _logger.info("IATC OAuth register: Returning registration response: %s", response_data)
        return Response(
            json.dumps(response_data),
            status=201,
            headers={"Content-Type": "application/json", **_CORS},
        )

    # ── MCP endpoint ──────────────────────────────────────────────────────────

    @http.route("/mcp", auth="none", csrf=False,
                methods=["GET", "POST", "OPTIONS"], type="http", save_session=False)
    def mcp_endpoint(self, **_kwargs):
        _logger.info("IATC MCP: /mcp endpoint called, method=%s", request.httprequest.method)
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
        _logger.info("IATC MCP: Accept header=%s, use_sse=%s", accept, use_sse)

        env, _cr = _open_env()
        _logger.info("IATC MCP: env opened=%s, db=%s", env is not None, env.cr.dbname if env else "None")
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
                "instructions": (
                    "When presenting treasury/cash data from this server, build a "
                    "branded 4-tab mobile dashboard artifact per the instructions "
                    "returned by get_treasury_report — do not present this data as "
                    "plain text or tables."
                ),
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

    # ── WhatsApp webhook (Twilio directo) ─────────────────────────────────────

    @http.route("/iatc/webhook/whatsapp-twilio", auth="none", csrf=False,
                methods=["POST"], type="http", save_session=False)
    def whatsapp_twilio_webhook(self, **kwargs):
        import threading
        import urllib.parse as _urlparse

        # Try all sources: werkzeug form, kwargs, raw body
        form = request.httprequest.form
        from_number = (form.get("From") or kwargs.get("From") or "").strip()
        body = (form.get("Body") or kwargs.get("Body") or "").strip()

        if not from_number or not body:
            raw = request.httprequest.get_data(cache=False)
            if raw:
                params = {k: v[0] for k, v in _urlparse.parse_qs(raw.decode("utf-8", errors="replace")).items()}
                from_number = from_number or params.get("From", "").strip()
                body = body or params.get("Body", "").strip()

        _logger.info("IATC WhatsApp webhook: From=%r Body=%r", from_number, body[:50] if body else "")

        def _twiml(text: str) -> Response:
            safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return Response(
                f"<Response><Message>{safe}</Message></Response>",
                status=200,
                headers={"Content-Type": "application/xml; charset=utf-8"},
            )

        if not from_number or not body:
            return _twiml("Error: mensaje vacío.")

        # ── Leer credenciales via cursor directo (fiable en auth="none") ──
        def _read_params():
            """Lee ir.config_parameter con cursor directo de Odoo Registry."""
            keys = [
                f"{_P}twilio_account_sid", f"{_P}twilio_auth_token",
                f"{_P}twilio_whatsapp_from", f"{_P}license_key",
                f"{_P}odoo_api_key", f"{_P}odoo_login",
                f"{_P}anthropic_api_key", f"{_P}claude_model",
                "web.base.url",
            ]
            defaults = {
                f"{_P}twilio_whatsapp_from": "whatsapp:+14155238886",
                f"{_P}odoo_login": "admin",
                f"{_P}claude_model": "claude-sonnet-4-6",
                "web.base.url": "",
            }
            result = dict(defaults)
            try:
                import odoo.service.db as _db_svc
                valid_dbs = _db_svc.list_dbs(True)
            except Exception:
                valid_dbs = []

            # Find db that has the module installed
            target_db = getattr(request, "db", None) or None
            if not target_db:
                for cand in valid_dbs:
                    try:
                        from odoo.modules.registry import Registry as _Reg
                        with _Reg(cand).cursor() as _c:
                            _c.execute(
                                "SELECT 1 FROM ir_module_module "
                                "WHERE name='ia_agents_treasury_control' AND state='installed'"
                            )
                            if _c.fetchone():
                                target_db = cand
                                break
                    except Exception:
                        continue

            if target_db:
                try:
                    from odoo.modules.registry import Registry as _Reg
                    with _Reg(target_db).cursor() as _c:
                        placeholders = ",".join(["%s"] * len(keys))
                        _c.execute(
                            f"SELECT key, value FROM ir_config_parameter WHERE key IN ({placeholders})",
                            keys,
                        )
                        for row in _c.fetchall():
                            result[row[0]] = row[1]
                except Exception as exc:
                    _logger.error("IATC WhatsApp: error reading config from %s: %s", target_db, exc)

            result["_db"] = target_db or ""
            _logger.info("IATC WhatsApp config: db=%s license_key=%r twilio_sid=%r",
                         result["_db"],
                         result.get(f"{_P}license_key", "")[:8],
                         result.get(f"{_P}twilio_account_sid", "")[:8])
            return result

        cfg = _read_params()
        twilio_sid    = cfg.get(f"{_P}twilio_account_sid", "")
        twilio_token  = cfg.get(f"{_P}twilio_auth_token", "")
        twilio_from   = cfg.get(f"{_P}twilio_whatsapp_from", "whatsapp:+14155238886")
        license_key   = cfg.get(f"{_P}license_key", "")
        odoo_api_key  = cfg.get(f"{_P}odoo_api_key", "")
        odoo_login    = cfg.get(f"{_P}odoo_login", "admin")
        anthropic_key = cfg.get(f"{_P}anthropic_api_key", "")
        claude_model  = cfg.get(f"{_P}claude_model", "claude-sonnet-4-6")
        odoo_url      = cfg.get("web.base.url", "").rstrip("/")
        odoo_db       = cfg.get("_db", "")

        # Si no hay API key de Anthropic, usar free trial (enviar null)
        anthropic_key_to_send = anthropic_key if anthropic_key else None

        def _send_twilio(to: str, text: str) -> None:
            """Envía un mensaje WhatsApp via Twilio REST API."""
            if not twilio_sid or not twilio_token:
                _logger.error("IATC WhatsApp: Twilio SID/Token no configurados")
                return
            payload = urllib.parse.urlencode({
                "From": twilio_from,
                "To": to,
                "Body": text[:1500],
            }).encode()
            tw_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            auth = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
            req = urllib.request.Request(
                tw_url, data=payload,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    _logger.info("IATC WhatsApp sent: %s", resp.status)
            except Exception as exc:
                _logger.error("IATC WhatsApp send error: %s", exc)

        def _process_and_reply():
            """Ejecuta la consulta en segundo plano y responde via Twilio API."""
            payload = json.dumps({
                "license_key": license_key,
                "operation": "process_whatsapp",
                "odoo_url": odoo_url,
                "odoo_db": odoo_db,
                "odoo_login": odoo_login,
                "odoo_api_key": odoo_api_key,
                "anthropic_api_key": anthropic_key_to_send,
                "claude_model": claude_model,
                "params": {"message": body, "from_number": from_number},
            }).encode("utf-8")
            req = urllib.request.Request(
                _AGENTS_EXECUTE, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read())
                    result = data.get("result", str(data))
            except urllib.error.HTTPError as exc:
                try:
                    detail = json.loads(exc.read()).get("detail", str(exc))
                except Exception:
                    detail = str(exc)
                _logger.error("IATC WhatsApp remote error: %s", detail)
                result = "Error al procesar tu consulta. Inténtalo de nuevo."
            except Exception as exc:
                _logger.error("IATC WhatsApp connection error: %s", exc)
                result = "No se pudo conectar con el servidor. Inténtalo más tarde."

            _send_twilio(from_number, result)

        # ── Responder a Twilio inmediatamente (< 5s) y procesar en background ──
        threading.Thread(target=_process_and_reply, daemon=True).start()

        ack = "⏳ Procesando tu consulta..." if body.lower() not in ("hola", "hi", "help", "ayuda") else (
            "Hola 👋 Soy tu asistente financiero de Odoo. Puedes preguntarme sobre:\n"
            "- Informe de tesoreria\n- Saldos bancarios\n- Estado IVA\n- Alertas\n- Facturas"
        )
        return _twiml(ack)
