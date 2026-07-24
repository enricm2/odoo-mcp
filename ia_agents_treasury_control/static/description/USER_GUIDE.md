# IA Treasury Control (MCP) — Guía Completa de Instalación y Configuración

**Versión:** 1.7.0 · **Compatibilidad:** Odoo 16, 17, 18, 19 y Odoo.sh

---

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Obtener tu licencia](#2-obtener-tu-licencia)
3. [Instalar el módulo en Odoo](#3-instalar-el-módulo-en-odoo)
4. [Configuración inicial](#4-configuración-inicial)
5. [Conectar con Claude (claude.ai)](#5-conectar-con-claude-claudeai)
6. [Conectar con Gemini (Google)](#6-conectar-con-gemini-google)
7. [Conectar con ChatGPT (OpenAI)](#7-conectar-con-chatgpt-openai)
8. [Conectar con WhatsApp (Twilio)](#8-conectar-con-whatsapp-twilio)
9. [Herramientas disponibles](#9-herramientas-disponibles)
10. [Ejemplos de uso](#10-ejemplos-de-uso)
11. [Scripts de instalación automática](#11-scripts-de-instalación-automática)
12. [Solución de problemas](#12-solución-de-problemas)

---

## 1. Requisitos previos

| Requisito | Detalle |
|-----------|---------|
| Odoo | Versión 16, 17, 18, 19 o Odoo.sh |
| Módulo `account` | Debe estar instalado (Contabilidad) |
| Acceso HTTPS | Tu Odoo debe ser accesible por HTTPS |
| Licencia | Adquirida en [apps.uniasser.net](https://apps.uniasser.net) |
| API key IA | Anthropic / Google / OpenAI (según el proveedor elegido) |
| **CRÍTICO:** `db_name` configurado en archivo de configuración de Odoo | Ver paso crítico abajo |

> ⚠️ **Importante:** El módulo NO almacena datos contables fuera de tu Odoo. La lógica de IA se ejecuta en servidores de Uniasser usando únicamente los datos que tú consultas en cada petición.

---

## 2. Obtener tu licencia

1. Ve a **[apps.uniasser.net](https://apps.uniasser.net)**
2. Elige el plan (mensual o anual) y completa el pago
3. Recibirás un email con tu clave con formato **`XXXX-XXXX-XXXX-XXXX`**
4. Guarda esta clave — la necesitarás en el paso 4

---

## 3. Instalar el módulo en Odoo

### Opción A — Odoo estándar (autohosting)

1. Descarga el ZIP correspondiente a tu versión:
   - Odoo 16: `ia_agents_treasury_control_odoo16_v16.0.1.7.3.zip`
   - Odoo 17: `ia_agents_treasury_control_odoo17_v17.0.1.7.3.zip`
   - Odoo 18: `ia_agents_treasury_control_odoo18_v18.0.1.7.3.zip`
   - Odoo 19: `ia_agents_treasury_control_odoo19_v19.0.1.7.3.zip`

2. En Odoo: **Ajustes → Activar modo desarrollador** (Ajustes → parte inferior de la página → "Activar modo desarrollador")

3. Ve a **Aplicaciones → Actualizar lista de aplicaciones**

4. Sube el ZIP: **Aplicaciones → Subir módulo** (icono de nube en la barra superior)

5. Busca `IA Treasury Control` y pulsa **Instalar**

### Opción B — Odoo.sh

1. Descarga el ZIP de tu versión (ver arriba)
2. En tu repositorio GitHub conectado a Odoo.sh, crea la carpeta `ia_agents_treasury_control` y sube el contenido del ZIP
3. O usa la opción de subida directa en el panel de Odoo.sh
4. Haz un commit/push para que Odoo.sh recargue los módulos
5. Ve a **Aplicaciones**, busca `IA Treasury Control` e instala

### Opción C — Línea de comandos (admin servidor)

```bash
# Copiar el módulo al directorio de addons
unzip ia_agents_treasury_control_odoo18_v18.0.1.7.0.zip -d /opt/odoo/custom-addons/

# Instalar (sustituye odoo18_db por tu base de datos)
sudo -u odoo python3 /opt/odoo/odoo-bin -c /etc/odoo.conf \
  -d odoo18_db -i ia_agents_treasury_control --stop-after-init
```

---

## 4. Configuración inicial

### ⚠️ PASO CRÍTICO: Configurar web.base.url

**ANTES de continuar, debes configurar la URL de tu Odoo.** Esto es obligatorio para que el servidor MCP funcione correctamente.

1. Ve a **Ajustes → Técnico → Parámetros del sistema**
2. Busca el parámetro `web.base.url`
3. Edítalo y pon la URL pública de tu Odoo con HTTPS:
   - **Ejemplo:** `https://odoo16.uniasser.net`
   - **Ejemplo:** `https://tudominio.com`
   - **Ejemplo:** `https://tu-odoo.sh.odoo.com` (si usas Odoo.sh)
4. **IMPORTANTE:** La URL debe empezar con `https://` (no `http://`)
5. Guarda los cambios

> ⚠️ **¿Por qué es esto necesario?**
> El módulo usa esta URL para generar los endpoints de OAuth que Claude.ai necesita para conectarse. Si no configuras esto correctamente, la conexión MCP fallará con errores de "sign-in service".

### ⚠️ PASO CRÍTICO: Configurar db_name en el archivo de configuración de Odoo

**ANTES de continuar, debes configurar el nombre de la base de datos en tu archivo de configuración de Odoo.** Esto es obligatorio para que el OAuth de MCP funcione correctamente.

1. Abre tu archivo de configuración de Odoo (típicamente `/etc/odoo.conf`, `/etc/odoo16.conf`, o similar)
2. Busca o añade el parámetro `db_name`
3. Establécelo al nombre exacto de tu base de datos:
   ```ini
   db_name = nombre_de_tu_base_de_datos
   ```
   - **Ejemplo:** `db_name = odood_db16CE`
   - **Ejemplo:** `db_name = mycompany_prod`
4. Guarda el archivo
5. **Reinicia Odoo** para que el cambio surta efecto

> ⚠️ **¿Por qué es esto necesario?**
> El flujo OAuth de MCP usa el nombre de la base de datos como OAuth Client ID. Si el `db_name` en tu archivo de configuración no coincide con el nombre real de tu base de datos, la autenticación OAuth fallará con errores "Authorization with the MCP server failed". Esto es especialmente importante para instalaciones autoalojadas donde pueden existir múltiples bases de datos.

---

Ve a **Ajustes → IA Treasury Control** (aparece en el menú lateral de Ajustes).

### 4.1 Licencia SaaS

| Campo | Valor |
|-------|-------|
| License key | Tu clave `XXXX-XXXX-XXXX-XXXX` |

Pulsa **"Validate license"** — debe aparecer ✅ Active con tu nombre.

### 4.2 Conexión Odoo (para agentes remotos)

El módulo necesita una API Key de Odoo para que el servidor de Uniasser pueda leer/escribir en tu Odoo.

**Método automático (recomendado):**
1. Pulsa **"Generate API Key automatically"**
2. Se genera y guarda automáticamente

**Método manual:**
1. Ve a **Ajustes → Usuarios → tu usuario → pestaña API Keys → Nueva clave**
2. Nombre: `IA Treasury Control MCP` · Scope: `RPC`
3. Copia la clave y pégala en el campo **Odoo API Key**
4. En **Odoo user (login)** escribe tu email de usuario de Odoo

### 4.3 Servidor MCP

| Campo | Descripción |
|-------|-------------|
| MCP Token | Generado automáticamente. Cópialo — lo necesitarás en el cliente IA |
| MCP Server URL | La URL de tu endpoint MCP (ej: `https://tuodoo.com/mcp`) |
| OAuth Client ID | El nombre de tu base de datos Odoo |

Si el token no está generado, pulsa **"Regenerate token"**.

> 💡 **Anota estos tres valores** — los usarás en los pasos 5, 6 y 7:
> - MCP Server URL
> - OAuth Client ID
> - MCP Token (OAuth Client Secret)

### 4.4 Proveedor de IA

Elige el proveedor y rellena su API Key:

| Proveedor | Dónde obtener la API Key |
|-----------|--------------------------|
| **Claude (Anthropic)** | [console.anthropic.com](https://console.anthropic.com) |
| **Gemini (Google)** | [aistudio.google.com](https://aistudio.google.com) · Tier gratuito disponible |
| **ChatGPT (OpenAI)** | [platform.openai.com](https://platform.openai.com) |
| **Grok (xAI)** | [console.x.ai](https://console.x.ai) |

---

## 5. Conectar con Claude (claude.ai)

### En Claude.ai (web)

1. Ve a **claude.ai → Settings → Integrations → Add MCP Server**
2. Rellena:
   - **Name:** `Odoo Treasury` (o el nombre que prefieras)
   - **URL:** el valor de **MCP Server URL** (ej: `https://tuodoo.com/mcp`)
   - **Authentication:** OAuth 2.0
   - **Client ID:** el valor de **OAuth Client ID** (nombre de tu BD)
   - **Client Secret:** el valor de **MCP Token**
3. Pulsa **Save** y luego **Connect**
4. Autoriza la conexión cuando Odoo te lo solicite

### En Claude Desktop (app Mac/Windows)

Edita el archivo de configuración:

- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo-treasury": {
      "url": "https://tuodoo.com/mcp",
      "authType": "oauth2",
      "clientId": "nombre_de_tu_bd",
      "clientSecret": "tu_mcp_token_aqui"
    }
  }
}
```

Reinicia Claude Desktop. Verás el icono 🔌 con "Odoo Treasury" conectado.

### Verificar la conexión

En cualquier chat de Claude, escribe:
> *"Usa odoo-treasury y ejecuta un health check"*

Respuesta esperada: `✅ MCP server online · Odoo connected`

---

## 6. Conectar con Gemini (Google)

### En Google AI Studio / Gemini API

Gemini puede conectarse vía MCP usando el cliente de Google:

1. Instala el CLI de Gemini si no lo tienes:
   ```bash
   npm install -g @google/gemini-cli
   ```

2. Configura el servidor MCP en `~/.gemini/config.json`:
   ```json
   {
     "mcpServers": {
       "odoo-treasury": {
         "url": "https://tuodoo.com/mcp",
         "authType": "oauth2",
         "clientId": "nombre_de_tu_bd",
         "clientSecret": "tu_mcp_token_aqui"
       }
     }
   }
   ```

3. Inicia el CLI:
   ```bash
   gemini
   ```

4. Pregunta directamente:
   > *"Muéstrame el informe de tesorería de este mes"*

### En Google Workspace (Gemini for Business)

Contacta con tu administrador de Google Workspace para añadir la integración MCP personalizada. El proceso es similar: URL + Client ID + Client Secret.

---

## 7. Conectar con ChatGPT (OpenAI)

### En ChatGPT (web / app)

ChatGPT Plus y Team soportan plugins y acciones personalizadas. Para conectar vía MCP:

1. Ve a **ChatGPT → Explore GPTs → Create a GPT**
2. En la sección **Actions → Add action**:
   - **Authentication:** OAuth
   - **Client ID:** nombre de tu BD de Odoo
   - **Client Secret:** tu MCP Token
   - **Auth URL:** `https://tuodoo.com/mcp/oauth/authorize`
   - **Token URL:** `https://tuodoo.com/mcp/oauth/token`
   - **Scope:** `mcp`
3. Importa el schema de la API desde:
   `https://tuodoo.com/mcp/.well-known/openapi.json`

### Con la API de OpenAI (desarrolladores)

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

# El módulo expone las herramientas como funciones compatibles con OpenAI
tools = [...]  # Obtener desde https://tuodoo.com/mcp/tools

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "¿Cuál es mi saldo bancario actual?"}],
    tools=tools
)
```

---

## 8. Conectar con WhatsApp (Twilio)

### 8.1 Crear cuenta Twilio

1. Regístrate en [twilio.com](https://www.twilio.com) (plan gratuito disponible)
2. En el panel de Twilio, ve a **Account → Account Info** y anota:
   - **Account SID** (empieza por `AC...`)
   - **Auth Token**
3. Ve a **Messaging → Try it out → Send a WhatsApp message**
4. Activa el **Sandbox de WhatsApp** y sigue las instrucciones para conectar tu número

### 8.2 Configurar en Odoo

En **Ajustes → IA Treasury Control → WhatsApp (Twilio)**:

| Campo | Valor |
|-------|-------|
| Twilio Account SID | Tu SID (AC...) |
| Twilio Auth Token | Tu token de autenticación |
| Twilio WhatsApp number | `whatsapp:+14155238886` (sandbox) o tu número dedicado |

Guarda y copia el valor del campo **Webhook URL for Twilio** — lo necesitas en el paso siguiente.

### 8.3 Configurar el Webhook en Twilio

1. En Twilio: **Messaging → Settings → WhatsApp Sandbox Settings**
2. En **"When a message comes in"**, pega la **Webhook URL** copiada de Odoo:
   ```
   https://tuodoo.com/iatc/webhook/whatsapp-twilio
   ```
3. Método: **HTTP POST**
4. Guarda

### 8.4 Probar

Envía un WhatsApp al número del sandbox de Twilio:
> *"Informe de tesorería"*

Recibirás la respuesta en WhatsApp en segundos.

---

## 9. Herramientas disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `get_treasury_report` | Informe completo de tesorería: saldos, cobros/pagos pendientes |
| `get_treasury_forecast` | Previsión de caja a 30, 60 y 90 días |
| `get_bank_account_balances` | Saldos de todas las cuentas bancarias |
| `get_bank_account_statement` | Extracto bancario desde una fecha |
| `get_account_ledger` | Libro mayor de cualquier cuenta contable |
| `get_customer_pending_invoices` | Facturas pendientes de cobro por cliente |
| `get_tax_status` | Estado fiscal trimestral: IVA e IRPF |
| `get_alerts` | Alertas: facturas vencidas, vencimientos fiscales, caja negativa |
| `create_draft_invoice` | Crear borrador de factura desde lenguaje natural |
| `process_email_invoices` | Procesar facturas recibidas por email (OCR) |
| `run_bank_reconciliation` | Propuestas de conciliación bancaria |
| `apply_reconciliation` | Aplicar conciliación aprobada |
| `create_timesheet_entry` | Registrar parte de horas |
| `create_timesheet_project` | Crear proyecto |
| `create_timesheet_task` | Crear tarea |
| `health_check` | Verificar que el servidor MCP y Odoo están operativos |

---

## 10. Ejemplos de uso

### Tesorería
> *"¿Cuál es mi situación de tesorería a cierre de hoy?"*
> *"Dame la previsión de caja para los próximos 90 días"*
> *"¿Qué facturas tengo pendientes de cobrar este mes?"*

### Contabilidad
> *"Muéstrame los movimientos de la cuenta 430000 desde enero"*
> *"¿Cuál es el saldo de mi cuenta bancaria del BBVA?"*

### Fiscal
> *"¿Cómo está el IVA del segundo trimestre?"*
> *"Dime si hay alguna alerta fiscal urgente"*

### Facturación
> *"Crea una factura de 1.500€ para ACME S.L. por consultoría de octubre"*
> *"Procesa las facturas que han llegado al email"*

### Conciliación
> *"Revisa los extractos bancarios pendientes de conciliar"*
> *"Aplica las conciliaciones que propones"*

### Partes de horas
> *"Registra 3 horas en el proyecto Marketing, tarea Diseño web, hoy"*

---

## 11. Scripts de instalación automática

### Mac / Linux

Guarda este script como `install_iatc.sh` y ejecútalo:

```bash
#!/bin/bash
# IA Treasury Control — Script de instalación automática
# Uso: bash install_iatc.sh

set -e

echo "=================================================="
echo "  IA Treasury Control — Instalador automático"
echo "=================================================="
echo ""

# Solicitar datos
read -p "URL de tu Odoo (ej: https://tuodoo.com): " ODOO_URL
read -p "Nombre de la base de datos de Odoo: " ODOO_DB
read -p "Email de administrador Odoo: " ODOO_EMAIL
read -s -p "Contraseña de administrador Odoo: " ODOO_PASS
echo ""
read -p "Versión de Odoo (16/17/18/19): " ODOO_VER

# Descargar módulo
ZIP_NAME="ia_agents_treasury_control_odoo${ODOO_VER}_v${ODOO_VER}.0.1.7.0.zip"
DOWNLOAD_URL="https://apps.uniasser.net/dl/${ZIP_NAME}"

echo ""
echo "▶ Descargando módulo ${ZIP_NAME}..."
curl -L -o "/tmp/${ZIP_NAME}" "${DOWNLOAD_URL}"
echo "✓ Descargado"

# Subir e instalar via API de Odoo
echo "▶ Subiendo módulo a Odoo..."

# Autenticar
SESSION=$(curl -s -c /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"model\":\"res.users\",\"method\":\"authenticate\",\"args\":[\"${ODOO_DB}\",\"${ODOO_EMAIL}\",\"${ODOO_PASS}\",{}],\"kwargs\":{}}}")

UID=$(echo "$SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])")

if [ -z "$UID" ] || [ "$UID" = "None" ]; then
  echo "❌ Error: no se pudo autenticar en Odoo. Verifica URL, base de datos y contraseña."
  exit 1
fi
echo "✓ Autenticado como UID=${UID}"

# Instalar módulo via ir.module.module
curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{
    \"model\":\"ir.module.module\",\"method\":\"update_list\",\"args\":[],\"kwargs\":{}}}" > /dev/null

MOD_ID=$(curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{
    \"model\":\"ir.module.module\",\"method\":\"search_read\",
    \"args\":[[[\"name\",\"=\",\"ia_agents_treasury_control\"]]],
    \"kwargs\":{\"fields\":[\"id\",\"state\"],\"limit\":1}}}" | \
  python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")

if [ -z "$MOD_ID" ]; then
  echo "⚠  Módulo no encontrado. Asegúrate de haber copiado el ZIP al directorio addons."
  echo "   Ruta sugerida: /opt/odoo/custom-addons/"
  echo "   Luego reinicia Odoo y vuelve a ejecutar este script."
  exit 1
fi

curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{
    \"model\":\"ir.module.module\",\"method\":\"button_immediate_install\",
    \"args\":[[${MOD_ID}]],\"kwargs\":{}}}" > /dev/null

echo "✓ Módulo instalado"

# Limpiar
rm -f /tmp/odoo_cookies.txt /tmp/${ZIP_NAME}

echo ""
echo "=================================================="
echo "  ✅ Instalación completada"
echo "=================================================="
echo ""
echo "Próximos pasos:"
echo "  1. Ve a Ajustes → IA Treasury Control"
echo "  2. Introduce tu licencia (XXXX-XXXX-XXXX-XXXX)"
echo "  3. Pulsa 'Generate API Key automatically'"
echo "  4. Copia el MCP Token y la MCP Server URL"
echo "  5. Configura tu cliente IA (Claude, Gemini, etc.)"
echo ""
echo "Guía completa: https://apps.uniasser.net/docs"
```

Para ejecutarlo:
```bash
chmod +x install_iatc.sh
bash install_iatc.sh
```

---

### Windows (PowerShell)

Guarda como `install_iatc.ps1` y ejecútalo en PowerShell como administrador:

```powershell
# IA Treasury Control — Instalador para Windows
# Ejecución: powershell -ExecutionPolicy Bypass -File install_iatc.ps1

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  IA Treasury Control — Instalador automático" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar datos
$OdooUrl  = Read-Host "URL de tu Odoo (ej: https://tuodoo.com)"
$OdooDb   = Read-Host "Nombre de la base de datos"
$OdooEmail = Read-Host "Email de administrador"
$OdooPass = Read-Host "Contraseña" -AsSecureString
$OdooPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($OdooPass))
$OdooVer  = Read-Host "Versión de Odoo (16/17/18/19)"

$ZipName = "ia_agents_treasury_control_odoo${OdooVer}_v${OdooVer}.0.1.7.0.zip"
$DownloadUrl = "https://apps.uniasser.net/dl/$ZipName"
$TmpZip = "$env:TEMP\$ZipName"

Write-Host ""
Write-Host "▶ Descargando módulo..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $DownloadUrl -OutFile $TmpZip
Write-Host "✓ Descargado" -ForegroundColor Green

# Autenticar en Odoo
Write-Host "▶ Conectando con Odoo..." -ForegroundColor Yellow

$AuthBody = @{
    jsonrpc = "2.0"
    method  = "call"
    params  = @{
        model  = "res.users"
        method = "authenticate"
        args   = @($OdooDb, $OdooEmail, $OdooPassPlain, @{})
        kwargs = @{}
    }
} | ConvertTo-Json -Depth 10

$Session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$AuthResp = Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" `
    -Body $AuthBody -WebSession $Session

$Uid = $AuthResp.result
if (-not $Uid) {
    Write-Host "❌ Error de autenticación. Verifica tus credenciales." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Autenticado (UID=$Uid)" -ForegroundColor Green

# Buscar e instalar el módulo
Write-Host "▶ Instalando módulo..." -ForegroundColor Yellow

$SearchBody = @{
    jsonrpc = "2.0"; method = "call"
    params  = @{
        model  = "ir.module.module"; method = "search_read"
        args   = @(@(@("name", "=", "ia_agents_treasury_control")))
        kwargs = @{ fields = @("id","state"); limit = 1 }
    }
} | ConvertTo-Json -Depth 10

$ModResp = Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" `
    -Body $SearchBody -WebSession $Session

if (-not $ModResp.result -or $ModResp.result.Count -eq 0) {
    Write-Host "⚠  Módulo no encontrado en Odoo." -ForegroundColor Yellow
    Write-Host "   Copia el ZIP al directorio addons de tu Odoo y reinicia el servicio." -ForegroundColor Yellow
    Write-Host "   ZIP guardado en: $TmpZip" -ForegroundColor Yellow
    exit 1
}

$ModId = $ModResp.result[0].id

$InstallBody = @{
    jsonrpc = "2.0"; method = "call"
    params  = @{
        model  = "ir.module.module"; method = "button_immediate_install"
        args   = @(@($ModId))
        kwargs = @{}
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" `
    -Body $InstallBody -WebSession $Session | Out-Null

Write-Host "✓ Módulo instalado correctamente" -ForegroundColor Green

# Limpiar
Remove-Item $TmpZip -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ✅ Instalación completada" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor White
Write-Host "  1. Ve a Ajustes → IA Treasury Control" -ForegroundColor White
Write-Host "  2. Introduce tu licencia (XXXX-XXXX-XXXX-XXXX)" -ForegroundColor White
Write-Host "  3. Pulsa 'Generate API Key automatically'" -ForegroundColor White
Write-Host "  4. Copia el MCP Token y la MCP Server URL" -ForegroundColor White
Write-Host "  5. Configura tu cliente IA (Claude, Gemini, etc.)" -ForegroundColor White
Write-Host ""
Write-Host "Guía completa: https://apps.uniasser.net/docs" -ForegroundColor Cyan
```

Para ejecutarlo, abre PowerShell como administrador:
```powershell
powershell -ExecutionPolicy Bypass -File install_iatc.ps1
```

---

## 12. Solución de problemas

### ❌ "License not found" al validar

- Verifica que copiaste la clave correctamente (formato `XXXX-XXXX-XXXX-XXXX`)
- Comprueba que tu Odoo tiene acceso a internet (el módulo llama a `apps.uniasser.net`)
- Si cambiaste de servidor, contacta soporte para transferir la licencia: soporte@uniasser.com

### ❌ "Authentication failed" en la conexión MCP

- El campo **Odoo user (login)** debe ser el email exacto del usuario (no el nombre)
- La API Key debe haberse generado en **esta instancia de Odoo** (no sirve la de otro servidor)
- Si usas Odoo.sh, el usuario puede ser diferente al de otras instancias

### ❌ "Authorization with the MCP server failed" o errores de "sign-in service"

- **CRÍTICO:** Verifica que `db_name` está configurado en tu archivo de configuración de Odoo (ej: `/etc/odoo.conf`).
- El parámetro `db_name` debe coincidir exactamente con el nombre real de tu base de datos.
- Ejemplo: `db_name = nombre_de_tu_base_de_datos`
- Reinicia Odoo después de cambiar el archivo de configuración.

### ❌ "301 Moved Permanently" en la conexión

Tu Odoo tiene `web.base.url` configurado con `http://` en lugar de `https://`. Corrígelo:
- **Ajustes → Técnico → Parámetros del sistema**
- Busca `web.base.url` y cámbialo a `https://tudominio.com`

### ❌ "This module cannot be uninstalled"

El módulo está en `server_wide_modules` del archivo de configuración de Odoo. Edita `/etc/odoo.conf`:
```ini
# Cambiar esto:
server_wide_modules = base,web,ia_agents_treasury_control
# Por esto:
server_wide_modules = base,web
```
Reinicia Odoo y ya podrás desinstalar.

### ❌ No aparece la sección en Ajustes

- Activa el modo desarrollador (Ajustes → parte inferior → "Activar modo desarrollador")
- Actualiza la lista de módulos (Aplicaciones → Actualizar lista)
- Haz click en **Actualizar** el módulo si ya estaba instalado

### ❌ "APIKeys._generate() got an unexpected keyword argument 'expiration_date'"

Tienes instalada una versión anterior del módulo. Actualiza a v1.7.0 o superior.

### ❌ WhatsApp no responde

- Verifica que la Webhook URL en Twilio coincide exactamente con la que aparece en Ajustes
- Comprueba que tu Odoo es accesible desde internet (Twilio necesita llamar a tu servidor)
- En el sandbox de Twilio, verifica que tu número sigue unido al sandbox (expira cada 72h)

### ℹ️ Contacto soporte

- Email: soporte@uniasser.com
- Web: [apps.uniasser.net](https://apps.uniasser.net)

---

*IA Treasury Control v1.7.0 · © 2026 Uniasser · Licencia OPL-1*

---

# IA Treasury Control (MCP) — Complete User Guide

**Version:** 1.7.0 · **Compatibility:** Odoo 16, 17, 18, 19 and Odoo.sh

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Get your license](#2-get-your-license)
3. [Install the module in Odoo](#3-install-the-module-in-odoo)
4. [Initial configuration](#4-initial-configuration)
5. [Connect with Claude (claude.ai)](#5-connect-with-claude-claudeai)
6. [Connect with Gemini (Google)](#6-connect-with-gemini-google)
7. [Connect with ChatGPT (OpenAI)](#7-connect-with-chatgpt-openai)
8. [Connect with WhatsApp (Twilio)](#8-connect-with-whatsapp-twilio)
8b. [Free Trial & Your Own Anthropic API Key](#8b-free-trial--your-own-anthropic-api-key)
9. [WhatsApp vs. AI Chat — Capabilities](#9-whatsapp-vs-ai-chat--capabilities)
10. [Available tools](#10-available-tools)
11. [Usage examples](#11-usage-examples)
12. [Auto-install scripts](#12-auto-install-scripts)
13. [Troubleshooting](#13-troubleshooting)
14. [Ubuntu Linux 24.04 — Self-hosted notes](#14-ubuntu-linux-2404--self-hosted-notes)

---

## 1. Prerequisites

| Requirement | Details |
|-------------|---------|
| Odoo | Version 16, 17, 18, 19 or Odoo.sh |
| `account` module | Must be installed (Accounting) |
| HTTPS access | Your Odoo must be reachable via HTTPS |
| License | Purchased at [apps.uniasser.net](https://apps.uniasser.net) |
| AI API key | **Optional** — a free trial (up to 5 €) is included. See section 8b. |
| **CRITICAL:** `db_name` configured in Odoo configuration file | See critical step below |

> ⚠️ **Important:** The module does NOT store accounting data outside your Odoo. All AI logic runs on Uniasser servers using only the data you query in each request.

---

## 2. Get your license

1. Go to **[apps.uniasser.net](https://apps.uniasser.net)**
2. Choose a plan (monthly or annual) and complete the payment
3. You will receive an email with your key in the format **`XXXX-XXXX-XXXX-XXXX`**
4. Save this key — you will need it in step 4

---

## 3. Install the module in Odoo

### Option A — Standard Odoo (self-hosted)

1. Download the ZIP for your version:
   - Odoo 16: `ia_agents_treasury_control_odoo16_v16.0.1.7.3.zip`
   - Odoo 17: `ia_agents_treasury_control_odoo17_v17.0.1.7.3.zip`
   - Odoo 18: `ia_agents_treasury_control_odoo18_v18.0.1.7.3.zip`
   - Odoo 19: `ia_agents_treasury_control_odoo19_v19.0.1.7.3.zip`

2. In Odoo: **Settings → Activate developer mode** (Settings → bottom of the page → "Activate developer mode")

3. Go to **Apps → Update apps list**

4. Upload the ZIP: **Apps → Upload module** (cloud icon in the top bar)

5. Search for `IA Treasury Control` and click **Install**

### Option B — Odoo.sh

1. Download the ZIP for your version (see above)
2. In your GitHub repository connected to Odoo.sh, create the folder `ia_agents_treasury_control` and upload the ZIP contents
3. Or use the direct upload option in the Odoo.sh dashboard
4. Commit/push so Odoo.sh reloads the modules
5. Go to **Apps**, search for `IA Treasury Control` and install

### Option C — Command line (server admin)

```bash
# Copy the module to the addons directory
unzip ia_agents_treasury_control_odoo18_v18.0.1.7.0.zip -d /opt/odoo/custom-addons/

# Install (replace odoo18_db with your database name)
sudo -u odoo python3 /opt/odoo/odoo-bin -c /etc/odoo.conf \
  -d odoo18_db -i ia_agents_treasury_control --stop-after-init
```

---

## 4. Initial configuration

### ⚠️ CRITICAL STEP: Configure web.base.url

**BEFORE proceeding, you MUST configure your Odoo URL.** This is mandatory for the MCP server to work correctly.

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

### ⚠️ CRITICAL STEP: Configure db_name in Odoo configuration file

**BEFORE proceeding, you MUST configure the database name in your Odoo configuration file.** This is mandatory for the MCP OAuth to work correctly.

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

Go to **Settings → IA Treasury Control** (shown in the Settings sidebar). Complete the five fields below in order. Total time: under 5 minutes.

> ⚠️ **You do NOT need your own AI API key to start.** New installations include a free trial (up to 5 € of AI usage on Uniasser's account). See section 8b for details.

---

### 4.1 License key

| Field | What to do |
|-------|------------|
| **License key** | Paste your `XXXX-XXXX-XXXX-XXXX` key (received by email from apps.uniasser.net) |

Click **"Validate license"**. You should see a green ✅ Active confirmation with your account name. If you see an error, check the key format and ensure your Odoo can reach the internet.

---

### 4.2 Odoo API Key

The module needs an Odoo API Key so that Uniasser's AI server can securely query your Odoo data.

Click **"Generate API Key automatically"** — the field fills in by itself. Do **not** generate or paste a key manually; the automatic button handles everything correctly.

---

### 4.3 MCP Token

The MCP Token is generated automatically when the module is installed. If the field is empty, click **"Regenerate token"**.

**Copy this value** — you will paste it into your AI client (Claude, etc.) in the next section.

---

### 4.4 MCP Server URL and OAuth Client ID

These two fields are filled in automatically:

| Field | Example value | What it is |
|-------|--------------|------------|
| **MCP Server URL** | `https://yourodoo.com/mcp` | The endpoint your AI client connects to |
| **OAuth Client ID** | `mycompany_prod` | Your Odoo database name |

**Copy both values** — you will need them when setting up Claude or another AI client.

---

### 4.5 Anthropic API Key (optional — skip if using free trial)

| Field | What to do |
|-------|------------|
| **Anthropic API Key** | Leave **blank** to use the free trial. Fill in only if you have your own key (see section 8b). |

Leave this field empty for now. The free trial (up to 5 € of AI usage) is used automatically.

Click **Save** when all fields are filled in.

---

**Summary of what you need to copy before moving on:**

| Value | Where to copy from |
|-------|--------------------|
| **MCP Token** | Settings → IA Treasury Control → MCP Token field |
| **MCP Server URL** | Settings → IA Treasury Control → MCP Server URL field |
| **OAuth Client ID** | Settings → IA Treasury Control → OAuth Client ID field |

---

## 5. Connect with Claude (claude.ai)

### On Claude.ai web — step by step

Before you start, make sure you have these three values from section 4:
- **MCP Server URL** (e.g. `https://yourodoo.com/mcp`)
- **OAuth Client ID** (your database name)
- **MCP Token**

**Steps:**

1. Go to **claude.ai** and log in
2. Click **Settings** (bottom-left of the screen)
3. Click **Integrations** in the left menu
4. Click **Add integration**
5. Fill in:
   - **Name:** `Odoo Treasury`
   - **URL:** paste your **MCP Server URL**
6. Click **Save** — the integration appears in the list
7. In any chat, click the **🔌 plug icon** (bottom of the message box) → select **Odoo Treasury**
8. Claude will ask you to connect — click **Authorize**
9. Odoo opens briefly to confirm — click **Allow**

Done. The 🔌 icon turns active. You can now ask Claude about your finances.

> 💡 **Tip:** If asked for Client ID or Client Secret during setup, enter the **OAuth Client ID** and **MCP Token** values from step 4 respectively.

### On Claude Desktop (Mac/Windows app)

Edit the configuration file:

- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo-treasury": {
      "url": "https://yourodoo.com/mcp",
      "authType": "oauth2",
      "clientId": "your_db_name",
      "clientSecret": "your_mcp_token_here"
    }
  }
}
```

Restart Claude Desktop. You will see the 🔌 icon with "Odoo Treasury" connected.

### Verify the connection

In any Claude chat, type:
> *"Use odoo-treasury and run a health check"*

Expected response: `✅ MCP server online · Odoo connected`

---

## 6. Connect with Gemini (Google)

### On Google AI Studio / Gemini API

1. Install the Gemini CLI if you don't have it:
   ```bash
   npm install -g @google/gemini-cli
   ```

2. Configure the MCP server in `~/.gemini/config.json`:
   ```json
   {
     "mcpServers": {
       "odoo-treasury": {
         "url": "https://yourodoo.com/mcp",
         "authType": "oauth2",
         "clientId": "your_db_name",
         "clientSecret": "your_mcp_token_here"
       }
     }
   }
   ```

3. Start the CLI:
   ```bash
   gemini
   ```

4. Ask directly:
   > *"Show me this month's treasury report"*

### On Google Workspace (Gemini for Business)

Contact your Google Workspace administrator to add the custom MCP integration. The process is similar: URL + Client ID + Client Secret.

---

## 7. Connect with ChatGPT (OpenAI)

### On ChatGPT (web / app)

ChatGPT Plus and Team support custom actions. To connect via MCP:

1. Go to **ChatGPT → Explore GPTs → Create a GPT**
2. In the **Actions → Add action** section:
   - **Authentication:** OAuth
   - **Client ID:** your Odoo DB name
   - **Client Secret:** your MCP Token
   - **Auth URL:** `https://yourodoo.com/mcp/oauth/authorize`
   - **Token URL:** `https://yourodoo.com/mcp/oauth/token`
   - **Scope:** `mcp`
3. Import the API schema from:
   `https://yourodoo.com/mcp/.well-known/openapi.json`

---

## 8. Connect with WhatsApp (Twilio)

### 8.1 Create a Twilio account

1. Sign up at [twilio.com](https://www.twilio.com) (free plan available)
2. In the Twilio dashboard, go to **Account → Account Info** and note:
   - **Account SID** (starts with `AC...`)
   - **Auth Token**
3. Go to **Messaging → Try it out → Send a WhatsApp message**
4. Activate the **WhatsApp Sandbox** and follow the instructions to connect your number

### 8.2 Configure in Odoo

In **Settings → IA Treasury Control → WhatsApp (Twilio)**:

| Field | Value |
|-------|-------|
| Twilio Account SID | Your SID (AC...) |
| Twilio Auth Token | Your authentication token |
| Twilio WhatsApp number | `whatsapp:+14155238886` (sandbox) or your dedicated number |

Save and copy the **Webhook URL for Twilio** — you need it in the next step.

### 8.3 Configure the Webhook in Twilio

1. In Twilio: **Messaging → Settings → WhatsApp Sandbox Settings**
2. In **"When a message comes in"**, paste the **Webhook URL** copied from Odoo:
   ```
   https://yourodoo.com/iatc/webhook/whatsapp-twilio
   ```
3. Method: **HTTP POST**
4. Save

### 8.4 Test

Send a WhatsApp to the Twilio sandbox number:
> *"Treasury report"*

You will receive the response on WhatsApp within seconds.

> ⚠️ **WhatsApp response time:** The first message after a period of inactivity may take up to 60 seconds. You will receive a "⏳ Processing..." reply immediately, and the actual answer arrives as a separate WhatsApp message shortly after.

> ⚠️ **Sandbox expiry:** The Twilio WhatsApp sandbox connection expires every 72 hours. If WhatsApp stops responding, re-send the join code (e.g. `join bright-flower`) to the Twilio sandbox number from your WhatsApp to reconnect.

---

## 8b. Free Trial & Your Own Anthropic API Key

### Free trial

Every new installation of IA Treasury Control includes a **free trial of up to 5 € of AI usage** on Uniasser's Anthropic account. During the trial:

- You do **not** need an Anthropic account or API key
- Leave the **Anthropic API Key** field in Settings completely blank
- All AI queries (Claude via MCP, WhatsApp bot) are handled automatically

When the free trial credit is exhausted, your queries will return a message explaining that the trial has ended and inviting you to add your own key.

### Getting your own Anthropic API key

To continue using IA Treasury Control without limits, get your own Anthropic API key:

1. Go to **[console.anthropic.com](https://console.anthropic.com)**
2. Click **Sign up** (free account — no credit card required to sign up)
3. Once logged in, go to **API Keys** in the left menu
4. Click **Create Key**
5. Give it a name like `Odoo Treasury`
6. Copy the key immediately — it starts with `sk-ant-...` and is shown **only once**
7. In Odoo: go to **Settings → IA Treasury Control**
8. Paste the key in the **Anthropic API Key** field
9. Click **Save**

> ⚠️ **Do not lose your key.** Anthropic shows it only when first created. If you lose it, generate a new one and update the Settings field.

### Anthropic pricing

Anthropic charges per use (pay-as-you-go, no monthly subscription required):

- **Typical business use:** €5–15 per month depending on query volume
- You can set spending limits in the Anthropic console to avoid surprises
- Billing dashboard: [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)

### If your key is invalid or expired

Go to **Settings → IA Treasury Control → Anthropic API Key**, clear the field, and click **Save**. The system will fall back to Uniasser's shared account (or the free trial if still active). Then generate a new key from console.anthropic.com and paste it in.

---

## 9. WhatsApp vs. AI Chat — Capabilities

The WhatsApp integration covers the most common financial queries via natural language. Here is a full comparison with the AI chat client (Claude, Gemini, ChatGPT):

| Capability | WhatsApp | AI Chat (MCP) |
|---|:---:|:---:|
| Treasury report | ✅ | ✅ |
| Cash flow forecast | ✅ | ✅ |
| Bank account balances | ✅ | ✅ |
| Bank statement (by account / date) | ✅ | ✅ |
| Account ledger (libro mayor) | ✅ | ✅ |
| VAT / IRPF tax status | ✅ | ✅ |
| Financial alerts (overdue, deadlines) | ✅ | ✅ |
| Pending invoices by customer | ✅ | ✅ |
| Create draft invoice | ✅ | ✅ |
| Log timesheet hours | ✅ | ✅ |
| Bank reconciliation proposals | ✅ | ✅ |
| Process email invoices (OCR) | ❌ | ✅ |
| Create projects / tasks | ❌ | ✅ |
| Apply reconciliation | ❌ | ✅ |
| Multi-turn conversation (context memory) | ✅ *| ✅ |
| Long detailed tables | ⚠️ summarised | ✅ full |

> *WhatsApp keeps a **30-minute session memory** per phone number (last 5 exchanges).
> This allows follow-up questions like *"What about that client?"* or *"Show me the same period for account 430"* without repeating context. After 30 minutes of inactivity the session resets.

> ⚠️ WhatsApp replies are capped at **1 500 characters**. Long reports are automatically summarised; ask the AI chat client for the full version if needed.

### Sample WhatsApp queries

```
Treasury report
VAT status
Bank balances
Statement for Bankinter from 01/05/2026
Pending invoices for Acme
Create invoice for Acme 1200 euros consulting
Log 2 hours on project Web, task Design
Financial alerts
Cash forecast
And that other client? (follow-up — uses session memory)
```

---

## 10. Available tools

| Tool | Description |
|------|-------------|
| `get_treasury_report` | Full treasury report: balances, receivables/payables |
| `get_treasury_forecast` | Cash flow forecast at 30, 60 and 90 days |
| `get_bank_account_balances` | Balances for all bank accounts |
| `get_bank_account_statement` | Bank statement from a given date |
| `get_account_ledger` | General ledger for any account |
| `get_customer_pending_invoices` | Outstanding receivables by customer |
| `get_tax_status` | Quarterly tax status: VAT and withholding tax |
| `get_alerts` | Alerts: overdue invoices, tax deadlines, negative cash |
| `create_draft_invoice` | Create a draft invoice from natural language |
| `process_email_invoices` | Process supplier invoices received by email (OCR) |
| `run_bank_reconciliation` | Bank reconciliation proposals |
| `apply_reconciliation` | Apply an approved reconciliation |
| `create_timesheet_entry` | Log a timesheet entry |
| `create_timesheet_project` | Create a project |
| `create_timesheet_task` | Create a task |
| `health_check` | Verify that the MCP server and Odoo are operational |

---

## 11. Usage examples

### Treasury
> *"What is my treasury position at end of today?"*
> *"Give me the cash forecast for the next 90 days"*
> *"Which invoices do I have pending collection this month?"*

### Accounting
> *"Show me movements for account 430000 since January"*
> *"What is the balance of my Santander bank account?"*

### Tax
> *"How is Q2 VAT looking?"*
> *"Are there any urgent tax alerts?"*

### Invoicing
> *"Create a 1,500 € invoice for ACME Ltd. for October consulting"*
> *"Process the invoices that arrived by email"*

### Reconciliation
> *"Review the pending bank statements to reconcile"*
> *"Apply the reconciliations you propose"*

### Timesheets
> *"Log 3 hours on the Marketing project, Web Design task, today"*

---

## 12. Auto-install scripts

### Mac / Linux

Save this script as `install_iatc.sh` and run it:

```bash
#!/bin/bash
# IA Treasury Control — Auto-install script
# Usage: bash install_iatc.sh

set -e

echo "=================================================="
echo "  IA Treasury Control — Auto Installer"
echo "=================================================="
echo ""

read -p "Your Odoo URL (e.g. https://yourodoo.com): " ODOO_URL
read -p "Odoo database name: " ODOO_DB
read -p "Odoo admin email: " ODOO_EMAIL
read -s -p "Odoo admin password: " ODOO_PASS
echo ""
read -p "Odoo version (16/17/18/19): " ODOO_VER

ZIP_NAME="ia_agents_treasury_control_odoo${ODOO_VER}_v${ODOO_VER}.0.1.7.0.zip"
DOWNLOAD_URL="https://apps.uniasser.net/dl/${ZIP_NAME}"

echo ""
echo "▶ Downloading ${ZIP_NAME}..."
curl -L -o "/tmp/${ZIP_NAME}" "${DOWNLOAD_URL}"
echo "✓ Downloaded"

echo "▶ Authenticating with Odoo..."
SESSION=$(curl -s -c /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"model\":\"res.users\",\"method\":\"authenticate\",\"args\":[\"${ODOO_DB}\",\"${ODOO_EMAIL}\",\"${ODOO_PASS}\",{}],\"kwargs\":{}}}")

UID=$(echo "$SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])")

if [ -z "$UID" ] || [ "$UID" = "None" ]; then
  echo "❌ Authentication failed. Check your URL, database name and password."
  exit 1
fi
echo "✓ Authenticated as UID=${UID}"

curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"model\":\"ir.module.module\",\"method\":\"update_list\",\"args\":[],\"kwargs\":{}}}" > /dev/null

MOD_ID=$(curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"model\":\"ir.module.module\",\"method\":\"search_read\",\"args\":[[[\"name\",\"=\",\"ia_agents_treasury_control\"]]],\"kwargs\":{\"fields\":[\"id\",\"state\"],\"limit\":1}}}" | \
  python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")

if [ -z "$MOD_ID" ]; then
  echo "⚠  Module not found. Make sure you copied the ZIP to the addons directory."
  exit 1
fi

curl -s -b /tmp/odoo_cookies.txt -X POST \
  "${ODOO_URL}/web/dataset/call_kw" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"model\":\"ir.module.module\",\"method\":\"button_immediate_install\",\"args\":[[${MOD_ID}]],\"kwargs\":{}}}" > /dev/null

rm -f /tmp/odoo_cookies.txt /tmp/${ZIP_NAME}

echo ""
echo "=================================================="
echo "  ✅ Installation complete"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Go to Settings → IA Treasury Control"
echo "  2. Enter your license key (XXXX-XXXX-XXXX-XXXX)"
echo "  3. Click 'Generate API Key automatically'"
echo "  4. Copy the MCP Token and MCP Server URL"
echo "  5. Configure your AI client (Claude, Gemini, etc.)"
echo ""
echo "Full guide: https://apps.uniasser.net/docs"
```

```bash
chmod +x install_iatc.sh && bash install_iatc.sh
```

---

### Windows (PowerShell)

```powershell
# IA Treasury Control — Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File install_iatc.ps1

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  IA Treasury Control — Auto Installer" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$OdooUrl   = Read-Host "Your Odoo URL (e.g. https://yourodoo.com)"
$OdooDb    = Read-Host "Database name"
$OdooEmail = Read-Host "Admin email"
$OdooPass  = Read-Host "Password" -AsSecureString
$OdooPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($OdooPass))
$OdooVer   = Read-Host "Odoo version (16/17/18/19)"

$ZipName = "ia_agents_treasury_control_odoo${OdooVer}_v${OdooVer}.0.1.7.0.zip"
$TmpZip  = "$env:TEMP\$ZipName"

Write-Host "▶ Downloading module..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://apps.uniasser.net/dl/$ZipName" -OutFile $TmpZip
Write-Host "✓ Downloaded" -ForegroundColor Green

$Session  = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$AuthBody = @{ jsonrpc="2.0"; method="call"; params=@{
    model="res.users"; method="authenticate"
    args=@($OdooDb,$OdooEmail,$OdooPassPlain,@{}); kwargs=@{} } } | ConvertTo-Json -Depth 10

$AuthResp = Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" -Body $AuthBody -WebSession $Session

if (-not $AuthResp.result) {
    Write-Host "❌ Authentication failed." -ForegroundColor Red; exit 1
}
Write-Host "✓ Authenticated" -ForegroundColor Green

$SearchBody = @{ jsonrpc="2.0"; method="call"; params=@{
    model="ir.module.module"; method="search_read"
    args=@(@(@("name","=","ia_agents_treasury_control")))
    kwargs=@{ fields=@("id","state"); limit=1 } } } | ConvertTo-Json -Depth 10

$ModResp = Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" -Body $SearchBody -WebSession $Session

if (-not $ModResp.result -or $ModResp.result.Count -eq 0) {
    Write-Host "⚠  Module not found. Copy the ZIP to your Odoo addons folder." -ForegroundColor Yellow
    exit 1
}

$InstBody = @{ jsonrpc="2.0"; method="call"; params=@{
    model="ir.module.module"; method="button_immediate_install"
    args=@(@($ModResp.result[0].id)); kwargs=@{} } } | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$OdooUrl/web/dataset/call_kw" `
    -Method POST -ContentType "application/json" -Body $InstBody -WebSession $Session | Out-Null

Remove-Item $TmpZip -ErrorAction SilentlyContinue
Write-Host "✅ Installation complete" -ForegroundColor Green
```

```powershell
powershell -ExecutionPolicy Bypass -File install_iatc.ps1
```

---

## 13. Troubleshooting

| Error / Symptom | Cause | Solution |
|-----------------|-------|----------|
| "License not found" | License key wrong format or not yet validated | Check key format is `XXXX-XXXX-XXXX-XXXX` → click **Validate license** in Settings |
| "401 invalid x-api-key" | Anthropic API key is invalid or expired | Go to **Settings → IA Treasury Control → Anthropic API Key** → clear the field → Save. This restores the free trial (or Uniasser shared key). Or paste a valid key from console.anthropic.com |
| "Authentication failed" (MCP) | Wrong login or API key | Use the exact Odoo user email; click **Generate API Key automatically** again |
| "Authorization with the MCP server failed" or "sign-in service" errors | `db_name` not configured or mismatched | **CRITICAL:** Check that `db_name` is configured in your Odoo configuration file (e.g., `/etc/odoo.conf`). The `db_name` parameter must match your actual database name exactly. Example: `db_name = your_database_name`. Restart Odoo after changing the configuration file. |
| "301 Moved Permanently" | `web.base.url` uses HTTP | Set `web.base.url` to `https://...` in **Settings → Technical → System Parameters** |
| Module cannot be uninstalled | Listed in `server_wide_modules` | Remove `ia_agents_treasury_control` from `/etc/odoo.conf` → `server_wide_modules`, then restart Odoo |
| Section not shown in Settings | Developer mode is off | Enable: **Settings → bottom of page → Activate developer mode** |
| WhatsApp does not reply | Takes up to 60 seconds on first query | Wait — a "⏳ Processing..." message arrives first; the real answer comes as a separate WhatsApp message |
| WhatsApp sandbox expired | Sandbox connection expires every 72 hours | Re-send the join code (e.g. `join bright-flower`) to the Twilio sandbox number from your WhatsApp |
| Claude says "No tools available" | Integration not connected in this chat | Click the 🔌 icon in the chat → select Odoo Treasury → Authorize |
| Free trial exhausted message | 5 € trial credit used up | Add your own Anthropic API key — see section 8b |

### Contact support

- Email: support@uniasser.com
- Web: [apps.uniasser.net](https://apps.uniasser.net)

---

---

## 14. Ubuntu Linux 24.04 — Self-hosted notes

If you are running Odoo on **Ubuntu 24.04 LTS** (self-hosted, not Odoo.sh), several extra steps are required that are not needed on Odoo.sh. This section summarises every issue found in practice and the exact fix.

---

### 14.1 Critical: set `db_name` in `/etc/odoo.conf`

**Symptom:** The MCP endpoint `/mcp` returns 404, or the WhatsApp webhook `/iatc/webhook/whatsapp-twilio` never responds, even though the module is installed.

**Cause:** When `db_name` is empty in the Odoo configuration file, Odoo does not register the custom routes from add-on modules at startup.

**Fix:** Open `/etc/odoo.conf` (or `/etc/odoo18.conf`) and set the database name explicitly:

```ini
[options]
db_name = your_database_name
```

Then restart Odoo:

```bash
sudo systemctl restart odoo
# or for Odoo 18:
sudo systemctl restart odoo18
```

> ⚠️ **This is the most common cause of the module appearing to be installed but not working at all.** Always check this first when routes are not responding.

---

### 14.2 `web.base.url` must be HTTPS

**Symptom:** MCP clients refuse to connect, or you get SSL/redirect errors.

**Cause:** The MCP protocol requires a secure HTTPS endpoint. If `web.base.url` starts with `http://`, it breaks the OAuth flow.

**Fix:** In Odoo, go to **Settings → Technical → Parameters → System Parameters** and set:

| Key | Value |
|-----|-------|
| `web.base.url` | `https://yourdomain.com` |

If you only have HTTP locally (e.g. during development), you must set up a reverse proxy with a valid SSL certificate (nginx + Let's Encrypt).

---

### 14.3 WhatsApp webhook — Twilio must reach port 8069

**Symptom:** WhatsApp messages arrive but no reply is ever sent; Twilio logs show connection errors or timeouts to your webhook URL.

**Cause:** Twilio calls the webhook URL (e.g. `https://yourdomain.com/iatc/webhook/whatsapp-twilio`) using HTTP POST. On a typical self-hosted Ubuntu setup, Odoo listens on port **8069**, and nginx proxies port 443 → 8069.

**Check:**
1. Your nginx config must proxy `/iatc/` to `http://127.0.0.1:8069`
2. Your firewall (ufw) must allow port 443 from outside

Quick nginx snippet (add inside the `server { listen 443 ... }` block):

```nginx
location /iatc/ {
    proxy_pass         http://127.0.0.1:8069;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_read_timeout 120s;
}
```

> ⚠️ **Set `proxy_read_timeout` to at least 120 seconds.** Twilio itself times out after 15 seconds (which is why the module sends an immediate "⏳ Processing..." reply and then sends the real answer as a second WhatsApp message). The 120-second nginx timeout ensures the background processing is not killed prematurely.

---

### 14.4 "401 invalid x-api-key" error

**Symptom:** Health check passes (Odoo connection is fine), but every AI query returns `401 invalid x-api-key`.

**Cause:** An Anthropic API key was previously saved in Settings that is now invalid, expired, or revoked. The module sends this stored key to the AI server, which rejects it.

**Fix (2 minutes):**

1. In Odoo: **Settings → IA Treasury Control → Artificial Intelligence**
2. Click **👁 View** next to **Anthropic API Key** — you will see the stored value
3. **Clear the field** (select all, delete) and click **Save**
4. The system automatically falls back to Uniasser's shared key (free trial)

If you want to use your own valid key instead:

1. Go to [console.anthropic.com](https://console.anthropic.com) → **API Keys → Create Key**
2. Name it `Odoo Treasury`, copy the key (starts with `sk-ant-...`)
3. Paste it in the **Anthropic API Key** field in Odoo Settings → Save

---

### 14.5 Odoo service user and PostgreSQL

On Ubuntu 24.04, Odoo typically runs as the `odoo` OS user, which uses **Unix socket peer authentication** to connect to PostgreSQL. This works by default and requires no password.

**Do not change** the PostgreSQL authentication method to `md5` or `scram-sha-256` for the `odoo` user — this would break the module's internal database reads. If you have changed it, revert `/etc/postgresql/16/main/pg_hba.conf` to:

```
local   all   odoo   peer
```

---

### 14.6 Quick self-hosted checklist

Run through this list whenever something is not working after installation:

| # | Check | How |
|---|-------|-----|
| 1 | `db_name` set in `/etc/odoo.conf` | `grep db_name /etc/odoo.conf` |
| 2 | Odoo service is running | `sudo systemctl status odoo` |
| 3 | `web.base.url` starts with `https://` | Odoo → Settings → Technical → System Parameters |
| 4 | nginx proxies `/iatc/` and `/mcp` to port 8069 | `nginx -T \| grep iatc` |
| 5 | Port 443 open in ufw | `sudo ufw status` |
| 6 | Anthropic API Key field is empty OR contains a valid `sk-ant-...` key | Odoo Settings → 👁 View |
| 7 | License validated (green ✅ in Settings) | Click **Validate license** |

---

*IA Treasury Control v1.7.0 · © 2026 Uniasser · OPL-1 License*
