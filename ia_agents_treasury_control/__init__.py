import os as _os, sys as _sys
# Añadir el directorio raíz del módulo a sys.path para que
# pyarmor_runtime_000000 (cifrado de license_manager) sea importable.
_MODULE_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _MODULE_DIR not in _sys.path:
    _sys.path.insert(0, _MODULE_DIR)


def _ensure_dependencies():
    import logging
    import subprocess
    import sys
    _log = logging.getLogger(__name__)
    packages = [
        ("anthropic",   "anthropic"),
        ("structlog",   "structlog"),
        ("httpx",       "httpx"),
        ("jwt",         "PyJWT"),
        ("cryptography","cryptography"),
        ("rapidfuzz",   "rapidfuzz"),
    ]
    missing = [pip for imp, pip in packages if not _importable(imp)]
    if missing:
        _log.info("ia_agents_treasury_control: instalando dependencias faltantes: %s", missing)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet"] + missing
            )
            _log.info("ia_agents_treasury_control: dependencias instaladas correctamente")
        except Exception as exc:
            _log.error("ia_agents_treasury_control: error instalando dependencias: %s", exc)


def _importable(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


_ensure_dependencies()

from . import models
from . import controllers


def post_init_hook(env_or_cr, registry=None):
    """Genera el token MCP automáticamente si no existe.

    Compatible con Odoo 16 (cr, registry) y Odoo 18+ (env).
    """
    import secrets
    # Odoo 16 passes (cr, registry); Odoo 17+ passes (env,)
    if registry is not None:
        # Odoo 16: build env from cursor
        import odoo.api
        env = odoo.api.Environment(env_or_cr, 1, {})
    else:
        env = env_or_cr
    icp = env["ir.config_parameter"].sudo()
    if not icp.get_param("ia_agents_treasury_control.mcp_secret_token", ""):
        icp.set_param(
            "ia_agents_treasury_control.mcp_secret_token",
            secrets.token_hex(32),
        )
