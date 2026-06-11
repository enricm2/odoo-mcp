{
    "name": "IA Treasury Control (MCP)",
    "version": "18.0.1.0.0",
    "summary": "AI agent for treasury, tax, invoices and timesheets via Claude MCP",
    "description": """
Connect your Odoo to Claude.ai and manage treasury, taxes, invoices and
timesheets using plain language.

Agent logic runs securely on Uniasser's servers. Compatible with Odoo 16,
17, 18, 19 and Odoo.sh.

Requires a SaaS license: https://apps.uniasser.net
    """,
    "author": "Uniasser",
    "website": "https://apps.uniasser.net",
    "category": "Accounting/Accounting",
    "depends": ["base", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/icon.png"],
    "license": "OPL-1",
    "application": True,
    "installable": True,
    "auto_install": False,
    "support": "soporte@uniasser.com",
}
