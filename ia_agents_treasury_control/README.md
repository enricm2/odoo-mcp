# IA Treasury Control — MCP Module for Odoo

> Manage your company's treasury, taxes, invoices and timesheets by talking to Claude.ai in plain language.
> Compatible with **Odoo 16, 17, 18, 19** and **Odoo.sh**.

---

## How it works

This module installs a lightweight MCP (Model Context Protocol) server inside your Odoo instance. When Claude.ai calls a tool, the module securely forwards the request to Uniasser's servers, which:

1. Validate your license
2. Connect to your Odoo via API key
3. Execute the requested agent (treasury, tax, invoices, timesheets...)
4. Return the result to Claude

**Your business logic never leaves the module** — the installed ZIP is a thin client with no embedded logic.

---

## Requirements

- Odoo 16, 17, 18, 19, or Odoo.sh
- A valid license key from [apps.uniasser.net](https://apps.uniasser.net)
- An Odoo API key (generated in Odoo settings — see step 3)
- *(Optional)* An Anthropic API key for AI-generated narrative reports

---

## Installation

### Step 1 — Install the module

**Option A: Upload ZIP (Odoo.sh or any Odoo)**

1. Download the ZIP for your Odoo version:
   - `ia_agents_treasury_control_odoo16_v16.0.1.0.0.zip`
   - `ia_agents_treasury_control_odoo17_v17.0.1.0.0.zip`
   - `ia_agents_treasury_control_odoo18_v18.0.1.0.0.zip`
   - `ia_agents_treasury_control_odoo19_v19.0.1.0.0.zip`

2. In Odoo, go to **Settings → Apps → Upload module** and select the ZIP.

3. Click **Install**.

**Option B: Self-hosted (manual)**

1. Extract the ZIP into your `custom-addons` folder.
2. Restart Odoo.
3. Go to **Settings → Apps → Update Apps List**.
4. Search for "IA Treasury Control" and click **Install**.

**Option C: Odoo.sh**

1. Add the module folder to your GitHub repository (in `custom-addons/`).
2. Push to your branch — Odoo.sh will install it automatically.

---

### Step 2 — Enter your license key

1. Go to **Settings → IA Treasury Control → License SaaS**
2. Enter your license key (format: `XXXX-XXXX-XXXX-XXXX`)
3. Click **Validate license** — the status should show **✅ Active**

If you don't have a license yet, get one at [apps.uniasser.net](https://apps.uniasser.net).

---

### Step 3 — Generate an Odoo API Key

The remote agent server needs read/write access to your Odoo to execute operations. This is done via an API key — no password is ever shared.

1. In Odoo, go to **Settings → Users & Companies → Users**
2. Open your user (or `admin`)
3. Scroll to the **API Keys** section
4. Click **New API Key**, give it a name (e.g. `IA Treasury Control`), and copy the key shown

> **Important:** The key is only shown once. Save it securely.

5. Go back to **Settings → IA Treasury Control → Connection with Odoo**
6. Paste the key in **Odoo API Key**
7. In **Odoo user (login)**, enter the login of the user whose key you generated (usually `admin`)

---

### Step 4 — Generate the MCP token

1. Go to **Settings → IA Treasury Control → MCP Server**
2. Click **Regenerate token** — a new token will be generated and saved
3. Note down the **MCP Server URL** shown (e.g. `https://yourodoo.com/mcp`)
4. Note down the **OAuth Client ID** shown (usually your database name)

---

### Step 5 — Connect Claude.ai

1. Go to [claude.ai](https://claude.ai) → **Settings → Integrations**
2. Click **Add MCP Server**
3. Fill in:
   - **MCP Server URL**: the URL from step 4 (e.g. `https://yourodoo.com/mcp`)
   - **OAuth Client ID**: the client ID from step 4
   - **OAuth Client Secret**: the MCP token from step 4
4. Click **Save** — Claude will verify the connection

---

### Step 6 (Optional) — Add your Anthropic API Key

Without this key, agents return structured data tables. With it, you get AI-generated narrative reports in natural language.

1. Get an API key at [console.anthropic.com](https://console.anthropic.com)
2. Go to **Settings → IA Treasury Control → Artificial Intelligence**
3. Paste the key in **Anthropic API Key (Claude)**

---

## Usage — Available Tools

Once connected, Claude.ai has access to these tools:

| Tool | What it does |
|------|-------------|
| `get_treasury_report` | Pending receivables, payables, and cash flow forecast |
| `get_tax_status` | VAT collected, VAT paid, IRPF withholdings by quarter |
| `create_draft_invoice` | Create a **draft** invoice in Odoo from natural language |
| `run_bank_reconciliation` | Propose matches between bank movements and open invoices |
| `apply_reconciliation` | Apply approved reconciliation matches |
| `process_email_invoices` | Read IMAP inbox, extract PDF invoices with OCR, create drafts |
| `create_timesheet_entry` | Log hours on a project/task |
| `create_timesheet_project` | Create a new project |
| `create_timesheet_task` | Create a new task in an existing project |
| `get_alerts` | Overdue invoices, upcoming tax deadlines, negative cash warnings |
| `get_account_ledger` | Debit/credit movements for any account (by code or name) |
| `get_customer_pending_invoices` | Unpaid customer invoices for a specific partner |
| `get_bank_account_balances` | Balances of all bank accounts (group 572) |
| `get_bank_account_statement` | Bank statement with running balance from a date |
| `health_check` | Verify the MCP server and Odoo connection are working |

### Example prompts

```
"Show me the treasury report for this month"

"How much VAT do I owe this quarter?"

"Create a draft invoice for Acme Corp, €1,200 for consulting services, today"

"Check if there are any bank movements I haven't matched"

"I worked 3.5 hours on the Website Redesign project today, task: Homepage"

"Are there any overdue invoices?"

"Show me the movements on account 4300 since January 1st"
```

---

## Security model

- **No logic in the module**: the installed ZIP contains only the MCP/OAuth protocol layer
- **API key stays in Odoo**: your Odoo credentials are stored in `ir.config_parameter`, encrypted by Odoo
- **HTTPS only**: all communication between the module and Uniasser servers uses TLS
- **License bound to your instance**: your license is validated against your database name on every request
- **Invoice creation is always a DRAFT**: no invoice is ever confirmed without explicit user approval
- **Reconciliation always requires approval**: the agent only proposes matches — you apply them

---

## Troubleshooting

### "License not configured"
→ Go to Settings → IA Treasury Control → License and enter your key.

### "Odoo API Key not configured"
→ Follow Step 3 above to generate and configure an API key.

### "Authentication failed. Check odoo_login and odoo_api_key"
→ Verify that the login name matches the user who generated the API key.
→ For Odoo.sh: use the user's **email address** as login, not just the username.

### "Could not connect to Uniasser server"
→ Check that your Odoo instance has outbound HTTPS access (port 443).
→ On-premise firewalls may block outbound requests — whitelist `apps.uniasser.net`.

### Claude says "MCP server unreachable"
→ Make sure your Odoo instance is accessible from the internet with a valid SSL certificate.
→ On Odoo.sh this is automatic. For self-hosted, configure a reverse proxy (nginx/Apache) with Let's Encrypt.

### Token expired in claude.ai
→ Go to Settings → IA Treasury Control → MCP Server → click **Regenerate token**.
→ Update the OAuth Client Secret in claude.ai with the new token.

---

## Updating the module

When a new version is available:

**Self-hosted:**
1. Replace the module folder with the new version
2. Run: `./odoo-bin -u ia_agents_treasury_control -d YOUR_DB`
3. Restart Odoo

**Odoo.sh:**
1. Push the updated module to your GitHub repository
2. Odoo.sh will update automatically

> **No reinstall needed** — the update command preserves all your configuration (license key, API key, MCP token).

---

## Support

- Website: [apps.uniasser.net](https://apps.uniasser.net)
- Email: soporte@uniasser.com
- Issues: [github.com/uniasser/ia-treasury-control](https://github.com/uniasser/ia-treasury-control)

---

## License

OPL-1 — Odoo Proprietary License v1.0  
© 2024-2026 Uniasser Sistemas SL
