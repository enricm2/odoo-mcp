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
- **CRITICAL:** `db_name` parameter configured in your Odoo configuration file (see critical step above)
- *(Optional)* An Anthropic API key for AI-generated narrative reports

---

## Installation

### ⚠️ CRITICAL: Configure web.base.url first

**BEFORE installing or configuring the module, you MUST configure your Odoo URL.** This is mandatory for the MCP server to work correctly.

1. Go to **Settings → Technical → System Parameters**
2. Search for the parameter `web.base.url`
3. Edit it and set your public Odoo URL with HTTPS:
   - **Example:** `https://odoo16.uniasser.net`
   - **Example:** `https://yourdomain.com`
   - **Example:** `https://your-odoo.sh.odoo.com` (if using Odoo.sh)
4. **IMPORTANT:** The URL must start with `https://` (not `http://`)
5. Save the changes

> ⚠️ **Why is this necessary?**
> The module uses this URL to generate the OAuth endpoints that Claude.ai needs to connect. If you don't configure this correctly, the MCP connection will fail with "sign-in service" errors.

### ⚠️ CRITICAL: Configure db_name in Odoo configuration file

**BEFORE installing or configuring the module, you MUST configure the database name in your Odoo configuration file.** This is mandatory for the MCP OAuth to work correctly.

1. Open your Odoo configuration file (typically `/etc/odoo.conf`, `/etc/odoo16.conf`, or similar)
2. Find or add the `db_name` parameter
3. Set it to your exact database name:
   ```ini
   db_name = your_database_name
   ```
   - **Example:** `db_name = odood_db16CE`
   - **Example:** `db_name = mycompany_prod`
4. Save the file
5. **Restart Odoo** for the change to take effect

> ⚠️ **Why is this necessary?**
> The MCP OAuth flow uses the database name as the OAuth Client ID. If the `db_name` in your configuration file doesn't match your actual database name, the OAuth authentication will fail with "Authorization with the MCP server failed" errors. This is especially important for self-hosted installations where multiple databases might exist.

---

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

### Step 7 (Optional) — Set up WhatsApp with Twilio

This lets your team query the financial agents by sending WhatsApp messages — no Claude.ai app needed.

#### Prerequisites

- A [Twilio](https://www.twilio.com) account (free trial available)
- Your Odoo instance reachable from the internet with a valid SSL certificate (HTTPS)

#### 7.1 — Get your Twilio credentials

1. Log in at [console.twilio.com](https://console.twilio.com)
2. On the main dashboard, note down:
   - **Account SID** — starts with `AC...`
   - **Auth Token** — click the eye icon to reveal it

#### 7.2 — Enable the WhatsApp Sandbox (for testing)

1. In Twilio console, go to **Messaging → Try it out → Send a WhatsApp message**
2. Follow the instructions to join the sandbox by sending `join <your-code>` to the Twilio number
3. This number (format `whatsapp:+14155238886`) is your sender number during testing

> For production, request a dedicated WhatsApp-enabled Twilio number.

#### 7.3 — Configure Twilio credentials in Odoo

1. Go to **Settings → IA Treasury Control → WhatsApp (Twilio)**
2. Fill in:
   - **Twilio Account SID**: the `AC...` value from step 7.1
   - **Twilio Auth Token**: the auth token from step 7.1
   - **Twilio WhatsApp number**: your sender number (e.g. `whatsapp:+14155238886`)
3. Click **Save** — the **Webhook URL for Twilio** field will auto-populate with your Odoo URL

#### 7.4 — Configure the webhook in Twilio

1. Copy the **Webhook URL for Twilio** shown in Odoo settings
   - It looks like: `https://yourodoo.com/iatc/webhook/whatsapp-twilio`
2. In Twilio console, go to **Messaging → Active numbers** (or **Sandbox settings** if testing)
3. In the field **"A message comes in"**, select **Webhook** and paste the URL
4. Method: **HTTP POST**
5. Click **Save**

#### 7.5 — Test it

Send a WhatsApp message to your Twilio number:
```
¿Cuál es el estado de la tesorería esta semana?
```

You should receive the treasury report directly in WhatsApp within a few seconds.

> **Note:** The webhook processes messages synchronously. Complex queries (reconciliation, email invoice processing) may take 10–30 seconds — this is normal.

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
 Go to Settings → IA Treasury Control → License and enter your key.

### "Odoo API Key not configured"
→ Follow Step 3 above to generate and configure an API key.

### "Authentication failed. Check odoo_login and odoo_api_key"
→ Verify that the login name matches the user who generated the API key.
→ For Odoo.sh: use the user's **email address** as login, not just the username.

### "Authorization with the MCP server failed" or "sign-in service" errors
→ **CRITICAL:** Check that `db_name` is configured in your Odoo configuration file (e.g., `/etc/odoo.conf`).
→ The `db_name` parameter must match your actual database name exactly.
→ Example: `db_name = your_database_name`
→ Restart Odoo after changing the configuration file.

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
