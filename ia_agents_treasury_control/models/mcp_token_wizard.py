"""Wizard transient para mostrar el token MCP en un campo grande."""
from odoo import fields, models


class MCPTokenWizard(models.TransientModel):
    _name = "iatc.mcp_token_wizard"
    _description = "MCP Token Wizard"

    token = fields.Text(string="MCP Token (OAuth Client Secret)", readonly=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        param_key = "ia_agents_treasury_control.mcp_secret_token"
        token = self.env["ir.config_parameter"].sudo().get_param(param_key, "")
        res["token"] = token
        return res
