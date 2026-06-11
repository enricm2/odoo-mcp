"""IA Treasury Control (MCP) — configuration settings."""
from __future__ import annotations

import secrets
import urllib.request
import json as _json

from odoo import api, fields, models

_P = "ia_agents_treasury_control."


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ── License ───────────────────────────────────────────────────────────────
    iatc_license_key = fields.Char(
        string="License key",
        config_parameter=f"{_P}license_key",
        help="SaaS subscription key. Format: XXXX-XXXX-XXXX-XXXX",
    )
    iatc_license_status = fields.Char(
        string="Status",
        compute="_compute_license_status",
        store=False,
    )
    iatc_license_customer = fields.Char(
        string="Customer",
        compute="_compute_license_status",
        store=False,
    )
    iatc_license_expires = fields.Char(
        string="Valid until",
        compute="_compute_license_status",
        store=False,
    )

    # ── MCP token and URL ─────────────────────────────────────────────────────
    iatc_mcp_secret_token = fields.Char(
        string="MCP Token (OAuth Client Secret)",
        config_parameter=f"{_P}mcp_secret_token",
        help="Paste this value in 'OAuth Client Secret' when adding the MCP server in claude.ai.",
    )
    iatc_mcp_endpoint_url = fields.Char(
        string="MCP Server URL",
        compute="_compute_mcp_info",
        store=False,
    )
    iatc_mcp_oauth_client_id = fields.Char(
        string="OAuth Client ID",
        compute="_compute_mcp_info",
        store=False,
    )

    # ── Odoo API Key (used by the remote agent server) ────────────────────────
    iatc_odoo_api_key = fields.Char(
        string="Odoo API Key",
        config_parameter=f"{_P}odoo_api_key",
        help=(
            "Odoo API key so the Uniasser server can read/write your Odoo data. "
            "Generate it at: Settings → Users → your user → API Keys → New Key."
        ),
    )
    iatc_odoo_login = fields.Char(
        string="Odoo user (login)",
        config_parameter=f"{_P}odoo_login",
        default="admin",
        help=(
            "Login of the user whose API Key you generated. Usually 'admin'. "
            "On Odoo.sh, use the user's email address."
        ),
    )

    # ── Anthropic API Key ─────────────────────────────────────────────────────
    iatc_anthropic_api_key = fields.Char(
        string="Anthropic API Key (Claude)",
        config_parameter=f"{_P}anthropic_api_key",
        help=(
            "Your Anthropic API key for AI-generated narrative reports. "
            "Get it at console.anthropic.com. "
            "Optional: without this key the module returns structured data tables."
        ),
    )
    iatc_claude_model = fields.Char(
        string="Claude model",
        config_parameter=f"{_P}claude_model",
        default="claude-sonnet-4-6",
    )

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends("iatc_mcp_secret_token")
    def _compute_mcp_info(self):
        icp = self.env["ir.config_parameter"].sudo()
        base_url = icp.get_param("web.base.url", "").rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        db_name = self.env.cr.dbname
        for rec in self:
            rec.iatc_mcp_endpoint_url = f"{base_url}/mcp"
            rec.iatc_mcp_oauth_client_id = db_name

    @api.depends("iatc_license_key")
    def _compute_license_status(self):
        for rec in self:
            key = self.env["ir.config_parameter"].sudo().get_param(
                f"{_P}license_key", ""
            )
            if not key:
                rec.iatc_license_status = "⚠️ Not configured"
                rec.iatc_license_customer = ""
                rec.iatc_license_expires = ""
                continue
            try:
                data = _json.dumps({
                    "license_key": key,
                    "instance_uuid": self.env.cr.dbname,
                    "module_version": "saas",
                }).encode()
                req = urllib.request.Request(
                    "https://apps.uniasser.net/licencias/api/v1/validate",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    info = _json.loads(resp.read())
                rec.iatc_license_status = "✅ Active"
                rec.iatc_license_customer = info.get("customer", "")
                rec.iatc_license_expires = info.get("expires", "")
            except Exception:
                rec.iatc_license_status = "❌ Inactive or expired"
                rec.iatc_license_customer = ""
                rec.iatc_license_expires = ""

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_validate_license(self):
        self._compute_license_status()
        status = self.iatc_license_status
        msg_type = "success" if "✅" in status else "warning"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "License validation",
                "message": f"{status} — {self.iatc_license_customer}",
                "type": msg_type,
                "sticky": False,
            },
        }

    def action_generate_mcp_token(self):
        token = secrets.token_hex(32)
        self.env["ir.config_parameter"].sudo().set_param(f"{_P}mcp_secret_token", token)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "MCP token regenerated",
                "message": "New token generated. Update the 'OAuth Client Secret' in claude.ai.",
                "type": "success",
                "sticky": False,
            },
        }

    def action_generate_odoo_api_key(self):
        """Genera automáticamente una Odoo API Key para el usuario actual y la guarda."""
        try:
            user = self.env.user
            # Eliminar clave anterior del módulo si existe
            existing_name = "IA Treasury Control MCP"
            self.env["res.users.apikeys"].sudo().search([
                ("user_id", "=", user.id),
                ("name", "=", existing_name),
            ]).unlink()
            # Generar nueva clave (sin sudo: _generate crea la clave para self.env.uid)
            key = self.env["res.users.apikeys"]._generate(
                scope="rpc",
                name=existing_name,
                expiration_date=False,
            )
            # Guardar en config
            icp = self.env["ir.config_parameter"].sudo()
            icp.set_param(f"{_P}odoo_api_key", key)
            icp.set_param(f"{_P}odoo_login", user.login)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "API Key generated",
                    "message": f"Odoo API Key generated for user '{user.login}' and saved automatically.",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as exc:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error generating API Key",
                    "message": str(exc),
                    "type": "danger",
                    "sticky": True,
                },
            }
