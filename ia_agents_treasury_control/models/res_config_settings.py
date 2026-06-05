"""Configuración del módulo IA Agents Treasury Control en Ajustes de Odoo."""

from __future__ import annotations

from odoo import api, fields, models

_P = "ia_agents_treasury_control."  # prefijo de parámetros


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ── Licencia ──────────────────────────────────────────────────────────────
    iatc_license_key = fields.Char(
        string="Clave de licencia",
        config_parameter=f"{_P}license_key",
        help="Clave de suscripción SaaS proporcionada por Uniasser. "
             "Formato: XXXX-XXXX-XXXX-XXXX",
    )
    iatc_license_status = fields.Char(
        string="Estado de la licencia",
        compute="_compute_license_status",
        store=False,
    )
    iatc_license_customer = fields.Char(
        string="Cliente registrado",
        compute="_compute_license_status",
        store=False,
    )
    iatc_license_expires = fields.Char(
        string="Válida hasta",
        compute="_compute_license_status",
        store=False,
    )

    # ── IA — Anthropic ────────────────────────────────────────────────────────
    iatc_anthropic_api_key = fields.Char(
        string="API Key Anthropic",
        config_parameter=f"{_P}anthropic_api_key",
        help="Clave de API de Anthropic (Claude). Obtenla en console.anthropic.com",
    )
    iatc_claude_model = fields.Char(
        string="Modelo Claude",
        config_parameter=f"{_P}claude_model",
        default="claude-sonnet-4-6",
        help="Modelo de Claude a utilizar. Por defecto: claude-sonnet-4-6",
    )

    # ── MCP — Seguridad ───────────────────────────────────────────────────────
    iatc_mcp_secret_token = fields.Char(
        string="Token MCP",
        config_parameter=f"{_P}mcp_secret_token",
        help="Token de autenticación generado automáticamente. "
             "Es el valor que debes pegar en el campo 'OAuth Client Secret' de claude.ai.",
    )
    iatc_mcp_endpoint_url = fields.Char(
        string="URL del servidor MCP",
        compute="_compute_mcp_info",
        store=False,
    )
    iatc_mcp_oauth_client_id = fields.Char(
        string="OAuth Client ID",
        compute="_compute_mcp_info",
        store=False,
    )

    # ── WhatsApp / webhook ────────────────────────────────────────────────────
    iatc_default_timesheet_email = fields.Char(
        string="Email por defecto (partes de horas)",
        config_parameter=f"{_P}default_timesheet_email",
        help="Email del usuario Odoo usado por defecto al registrar partes de horas "
             "desde WhatsApp cuando no se especifica usuario.",
    )
    iatc_whatsapp_token = fields.Char(
        string="Token de acceso Meta",
        config_parameter=f"{_P}whatsapp_token",
        help="Token de acceso permanente de la app de Meta (Graph API). "
             "Meta for Developers → Tu app → WhatsApp → API Setup.",
    )
    iatc_whatsapp_phone_id = fields.Char(
        string="ID de teléfono (Phone ID)",
        config_parameter=f"{_P}whatsapp_phone_id",
        help="Identificador numérico del número de teléfono en Meta. Ej: 1201254209727479",
    )
    iatc_whatsapp_default_number = fields.Char(
        string="Número destino por defecto",
        config_parameter=f"{_P}whatsapp_default_number",
        help="Número al que se envían los informes cuando no se especifica uno. "
             "Formato internacional sin '+': 34685525090",
    )

    # ── Open Banking — Nordigen ───────────────────────────────────────────────
    iatc_nordigen_secret_id = fields.Char(
        string="Nordigen Secret ID",
        config_parameter=f"{_P}nordigen_secret_id",
        help="Secret ID de GoCardless Open Banking (Nordigen). Gratuito para España/UE.",
    )
    iatc_nordigen_secret_key = fields.Char(
        string="Nordigen Secret Key",
        config_parameter=f"{_P}nordigen_secret_key",
    )

    # ── Open Banking — Plaid (alternativa) ───────────────────────────────────
    iatc_plaid_client_id = fields.Char(
        string="Plaid Client ID",
        config_parameter=f"{_P}plaid_client_id",
    )
    iatc_plaid_secret = fields.Char(
        string="Plaid Secret",
        config_parameter=f"{_P}plaid_secret",
    )
    iatc_plaid_env = fields.Selection(
        selection=[
            ("sandbox", "Sandbox (pruebas)"),
            ("development", "Development"),
            ("production", "Production"),
        ],
        string="Entorno Plaid",
        config_parameter=f"{_P}plaid_env",
        default="sandbox",
    )

    # ── Email IMAP (facturas recibidas) ───────────────────────────────────────
    iatc_imap_host = fields.Char(
        string="Host IMAP",
        config_parameter=f"{_P}imap_host",
        default="imap.gmail.com",
    )
    iatc_imap_user = fields.Char(
        string="Usuario IMAP",
        config_parameter=f"{_P}imap_user",
    )
    iatc_imap_password = fields.Char(
        string="Contraseña IMAP",
        config_parameter=f"{_P}imap_password",
    )
    iatc_imap_folder = fields.Char(
        string="Carpeta IMAP",
        config_parameter=f"{_P}imap_folder",
        default="Facturas",
        help="Nombre de la carpeta IMAP donde llegan las facturas de proveedores.",
    )

    # ── Desarrollo ────────────────────────────────────────────────────────────
    iatc_dev_mode = fields.Boolean(
        string="Modo desarrollo (omitir licencia)",
        config_parameter=f"{_P}dev_mode",
        default=False,
        help="Activa para probar el módulo sin licencia. DESACTIVAR en producción.",
    )

    # ── Umbrales ──────────────────────────────────────────────────────────────
    iatc_forecast_days = fields.Integer(
        string="Días de previsión de caja",
        config_parameter=f"{_P}forecast_days",
        default=30,
    )
    iatc_reconciliation_threshold = fields.Float(
        string="Confianza mínima de conciliación",
        config_parameter=f"{_P}reconciliation_threshold",
        default=0.75,
        help="Porcentaje mínimo de confianza (0.0–1.0) para proponer un match bancario.",
    )
    iatc_tax_alert_pct = fields.Float(
        string="% alerta variación fiscal",
        config_parameter=f"{_P}tax_alert_pct",
        default=0.15,
        help="Variación respecto al trimestre anterior que dispara alerta fiscal.",
    )

    # ── Computed: estado de licencia ──────────────────────────────────────────

    @api.depends("iatc_mcp_secret_token")
    def _compute_mcp_info(self):
        icp = self.env["ir.config_parameter"].sudo()
        base_url = icp.get_param("web.base.url", "").rstrip("/")
        # Forzar HTTPS en la URL mostrada
        base_url = base_url.replace("http://", "https://", 1) if base_url.startswith("http://") else base_url
        db_name = self.env.cr.dbname
        for rec in self:
            rec.iatc_mcp_endpoint_url = f"{base_url}/mcp"
            rec.iatc_mcp_oauth_client_id = db_name

    @api.depends("iatc_license_key")
    def _compute_license_status(self):
        from .license_manager import get_license_info
        for rec in self:
            info = get_license_info(rec.env)
            if info["valid"]:
                rec.iatc_license_status = "✅ Activa"
            elif not info["key_configured"]:
                rec.iatc_license_status = "⚠️ Sin configurar"
            else:
                rec.iatc_license_status = "❌ Inactiva o caducada"
            rec.iatc_license_customer = info.get("customer", "")
            rec.iatc_license_expires = info.get("expires", "")

    # ── Acciones ──────────────────────────────────────────────────────────────

    def action_validate_license(self):
        """Botón 'Validar licencia ahora' — fuerza renovación online."""
        from .license_manager import check_license
        # Borrar token cacheado para forzar validación online
        self.env["ir.config_parameter"].sudo().set_param(
            "ia_agents_treasury_control.license_token", ""
        )
        valid, customer, message = check_license(self.env)
        msg_type = "success" if valid else "warning"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Validación de licencia",
                "message": message,
                "type": msg_type,
                "sticky": False,
            },
        }

    def action_generate_mcp_token(self):
        """Genera un nuevo token MCP aleatorio y lo guarda."""
        import secrets
        token = secrets.token_hex(32)
        self.env["ir.config_parameter"].sudo().set_param(
            f"{_P}mcp_secret_token", token
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Token regenerado",
                "message": "Se ha generado un nuevo token MCP. "
                           "Actualiza el 'OAuth Client Secret' en claude.ai con el nuevo valor.",
                "type": "success",
                "sticky": False,
            },
        }
