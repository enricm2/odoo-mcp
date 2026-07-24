"""IA Treasury Control (MCP) — configuration settings."""
from __future__ import annotations

import logging
import secrets
import urllib.request
import json as _json

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
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
    iatc_mcp_database = fields.Selection(
        selection="_get_available_databases",
        string="MCP Database",
        config_parameter=f"{_P}mcp_database",
        help="Select the database to use for MCP OAuth. This is required for OAuth endpoints to work correctly.",
    )
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

    # ── AI Provider ───────────────────────────────────────────────────────────
    iatc_llm_provider = fields.Selection(
        selection=[
            ("claude", "Claude (Anthropic)"),
            ("gemini", "Gemini (Google)"),
            ("openai", "ChatGPT (OpenAI)"),
            ("grok", "Grok (xAI)"),
        ],
        string="Active AI provider",
        config_parameter=f"{_P}llm_provider",
        default="claude",
        help="Choose which AI provider generates reports and processes invoices.",
    )

    # ── Claude ────────────────────────────────────────────────────────────────
    iatc_anthropic_api_key = fields.Char(
        string="Anthropic API Key (Claude)",
        config_parameter=f"{_P}anthropic_api_key",
        help="Get it at console.anthropic.com. Required if provider is Claude.",
    )
    iatc_claude_model = fields.Char(
        string="Claude model",
        config_parameter=f"{_P}claude_model",
        default="claude-sonnet-4-6",
    )

    # ── Gemini ────────────────────────────────────────────────────────────────
    iatc_gemini_api_key = fields.Char(
        string="Gemini API Key (Google)",
        config_parameter=f"{_P}gemini_api_key",
        help="Get it at aistudio.google.com. Free tier available. Required if provider is Gemini.",
    )
    iatc_gemini_model = fields.Char(
        string="Gemini model",
        config_parameter=f"{_P}gemini_model",
        default="gemini-2.0-flash",
    )

    # ── OpenAI ────────────────────────────────────────────────────────────────
    iatc_openai_api_key = fields.Char(
        string="OpenAI API Key (ChatGPT)",
        config_parameter=f"{_P}openai_api_key",
        help="Get it at platform.openai.com. Required if provider is ChatGPT.",
    )
    iatc_openai_model = fields.Char(
        string="OpenAI model",
        config_parameter=f"{_P}openai_model",
        default="gpt-4o",
    )

    # ── Grok ──────────────────────────────────────────────────────────────────
    iatc_grok_api_key = fields.Char(
        string="Grok API Key (xAI)",
        config_parameter=f"{_P}grok_api_key",
        help="Get it at console.x.ai. Required if provider is Grok.",
    )
    iatc_grok_model = fields.Char(
        string="Grok model",
        config_parameter=f"{_P}grok_model",
        default="grok-3",
    )

    # ── WhatsApp (Twilio) ─────────────────────────────────────────────────────
    iatc_twilio_account_sid = fields.Char(
        string="Account SID",
        config_parameter=f"{_P}twilio_account_sid",
        help="From Twilio console → Account Info. Starts with AC...",
    )
    iatc_twilio_auth_token = fields.Char(
        string="Auth Token",
        config_parameter=f"{_P}twilio_auth_token",
        help="From Twilio console → Account Info.",
    )
    iatc_twilio_whatsapp_from = fields.Char(
        string="WhatsApp sender number",
        config_parameter=f"{_P}twilio_whatsapp_from",
        default="whatsapp:+14155238886",
        help="Format: whatsapp:+1XXXXXXXXXX",
    )
    iatc_whatsapp_webhook_url = fields.Char(
        string="Webhook URL",
        readonly=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────────

    def _get_available_databases(self):
        """Return list of available databases for the selection field."""
        try:
            import odoo.service.db as db_service
            dbs = db_service.list_dbs(True)
            return [(db, db) for db in dbs]
        except Exception:
            # Fallback: return current database
            return [(self.env.cr.dbname, self.env.cr.dbname)]

    @api.depends("iatc_mcp_secret_token", "iatc_mcp_database")
    def _compute_mcp_info(self):
        icp = self.env["ir.config_parameter"].sudo()
        base_url = icp.get_param("web.base.url", "").rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        for rec in self:
            rec.iatc_mcp_endpoint_url = f"{base_url}/mcp"
            # Use configured MCP database if set, otherwise fall back to current database
            db_name = rec.iatc_mcp_database or self.env.cr.dbname
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
                    "module_version": "16.0.1.7.1",
                }).encode()
                req = urllib.request.Request(
                    "https://apps.uniasser.net/licencias/api/v1/validate",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    info = _json.loads(resp.read())
                rec.iatc_license_status = "✅ Active"
                rec.iatc_license_customer = info.get("customer", "")
                rec.iatc_license_expires = info.get("expires", "")
            except urllib.error.HTTPError as exc:
                _logger.error("License validation HTTP error: %s", exc)
                try:
                    error_detail = _json.loads(exc.read()).get("detail", str(exc))
                    rec.iatc_license_status = f"❌ Error: {error_detail}"
                except Exception:
                    rec.iatc_license_status = f"❌ HTTP {exc.code}"
                rec.iatc_license_customer = ""
                rec.iatc_license_expires = ""
            except Exception as exc:
                _logger.error("License validation error: %s", exc)
                rec.iatc_license_status = "❌ Connection error"
                rec.iatc_license_customer = ""
                rec.iatc_license_expires = ""

    # ── get/set values ────────────────────────────────────────────────────────

    def get_values(self):
        res = super().get_values()
        icp = self.env["ir.config_parameter"].sudo()
        base_url = icp.get_param("web.base.url", "").rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        res["iatc_whatsapp_webhook_url"] = f"{base_url}/iatc/webhook/whatsapp-twilio"
        return res

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

    # ── View (reveal) actions for sensitive fields ─────────────────────────────

    def _reveal(self, param_name: str, label: str):
        """Generic helper: show a sensitive config value in a notification popup."""
        val = self.env["ir.config_parameter"].sudo().get_param(param_name, "")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"🔑 {label}",
                "message": val if val else "(not configured)",
                "type": "info",
                "sticky": True,
            },
        }

    def action_view_license_key(self):
        return self._reveal(f"{_P}license_key", "License Key")

    def action_view_odoo_api_key(self):
        return self._reveal(f"{_P}odoo_api_key", "Odoo API Key")

    def action_view_anthropic_api_key(self):
        return self._reveal(f"{_P}anthropic_api_key", "Anthropic API Key")

    def action_view_gemini_api_key(self):
        return self._reveal(f"{_P}gemini_api_key", "Gemini API Key")

    def action_view_openai_api_key(self):
        return self._reveal(f"{_P}openai_api_key", "OpenAI API Key")

    def action_view_grok_api_key(self):
        return self._reveal(f"{_P}grok_api_key", "Grok API Key")

    def action_view_twilio_account_sid(self):
        return self._reveal(f"{_P}twilio_account_sid", "Twilio Account SID")

    def action_view_twilio_auth_token(self):
        return self._reveal(f"{_P}twilio_auth_token", "Twilio Auth Token")

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
            # Odoo 16 signature: _generate(scope, name)
            # Odoo 17+ signature: _generate(scope, name, expiration_date=False)
            try:
                key = self.env["res.users.apikeys"]._generate(
                    scope="rpc",
                    name=existing_name,
                    expiration_date=False,
                )
            except TypeError:
                key = self.env["res.users.apikeys"]._generate(
                    scope="rpc",
                    name=existing_name,
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
