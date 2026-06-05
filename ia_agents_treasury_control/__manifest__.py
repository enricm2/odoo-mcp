# © 2024-2026 Uniasser Consulting S.L. — Todos los derechos reservados.
# Licencia comercial de suscripción SaaS. Queda expresamente prohibida
# la copia, redistribución, modificación o ingeniería inversa sin autorización escrita.
# Véase LICENSE.md para los términos completos y las cláusulas penales aplicables.

{
    "name": "IA Agents Treasury Control",
    "summary": "Agentes de IA financieros para tesorería, fiscalidad, contabilidad y partes de horas",
    "description": """
IA Agents Treasury Control — Uniasser Consulting S.L.
======================================================
Conecta claude.ai directamente con tu Odoo para gestionar tesorería,
fiscalidad, facturas y partes de horas desde lenguaje natural.

Solo tienes que preguntar — Claude consulta Odoo y te responde con los
datos reales de tu empresa. Todo queda en borrador: nunca se confirma
ni envía nada sin tu aprobación.

CONFIGURACIÓN EN 3 PASOS
-------------------------
1. Instala el módulo y activa la licencia:
   Ajustes → IA Treasury Control → Licencia SaaS
   Introduce tu clave (formato XXXX-XXXX-XXXX-XXXX) y pulsa «Validar».

2. Copia los datos de conexión desde Odoo:
   Ajustes → IA Treasury Control → Conectar con claude.ai
   Verás la URL del servidor, OAuth Client ID y OAuth Client Secret
   generados automáticamente.

3. Añade el conector en claude.ai:
   Settings → Integrations → Add custom connector
   Pega la URL, Client ID y Client Secret del paso anterior.

HERRAMIENTAS DISPONIBLES (14 herramientas MCP)
-----------------------------------------------
Tesorería y caja
  - get_treasury_report        Cobros/pagos pendientes y previsión de caja
  - get_bank_account_balances  Saldos de todas las cuentas bancarias
  - get_bank_account_statement Extracto bancario con saldo arrastrado

Fiscal
  - get_tax_status             IVA, IRPF y estimación IS por trimestre

Facturas y clientes
  - create_draft_invoice           Factura de cliente en borrador
  - process_email_invoices         OCR de PDFs del buzón → borrador factura proveedor
  - get_customer_pending_invoices  Facturas pendientes de cobro de un cliente
  - get_account_ledger             Libro mayor de cualquier cuenta contable

Conciliación bancaria (requiere Nordigen/Plaid, opcional)
  - run_bank_reconciliation    Propone matches movimientos ↔ facturas
  - apply_reconciliation       Crea pagos borrador para los matches aprobados

Alertas
  - get_alerts                 Vencidos, plazos fiscales, caja negativa

Partes de horas
  - create_timesheet_entry     Registra parte de horas (proyecto/tarea/usuario)
  - create_timesheet_project   Crea un proyecto en Odoo
  - create_timesheet_task      Crea una tarea dentro de un proyecto

Sistema
  - health_check               Comprueba la conexión con Odoo

EJEMPLOS DE USO (desde Claude)
-------------------------------
«¿Cómo está la tesorería esta semana?»
«Dame el estado del IVA del Q1 de 2025»
«Crea una factura a Empresa ABC por 1.500 € de consultoría»
«Concilia los movimientos bancarios de los últimos 15 días»
«¿Hay alguna alerta financiera importante hoy?»
«Registra 3 horas de diseño web en el proyecto Cliente XYZ para ana@empresa.com»
«¿Cuánto dinero tenemos en el banco ahora mismo?»
«¿Qué facturas tiene pendientes el cliente García S.L.?»

REQUISITOS TÉCNICOS
-------------------
- nginx: añadir proxy_buffering off para /mcp (ver guía en la descripción HTML)
- Python: anthropic, structlog, httpx, PyJWT, cryptography, rapidfuzz
- Requiere suscripción SaaS activa

Soporte: info@uniasser.com
Web:     https://www.uniasser.com
    """,
    "version": "17.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Uniasser Consulting S.L.",
    "website": "https://www.uniasser.com",
    "support": "info@uniasser.com",
    "maintainer": "Uniasser Consulting S.L.",
    "license": "OPL-1",  # Odoo Proprietary License v1
    "depends": [
        "base",
        "account",
        "project",
        "hr_timesheet",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {
        "python": [
            "anthropic",
            "structlog",
            "httpx",
            "jwt",
            "cryptography",
            "rapidfuzz",
        ],
    },
    "images": ["static/src/img/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
    "price": 189.00,
    "currency": "EUR",
}
