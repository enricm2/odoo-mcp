import urllib.parse, urllib.request, json, webbrowser, http.server, threading, sys

print("=== Gmail OAuth - Obtener Refresh Token ===")
print()
cid = input("Client ID: ").strip()
csec = input("Client Secret: ").strip()
redir = "http://127.0.0.1:9085/callback"
scope = "https://www.googleapis.com/auth/gmail.readonly"
code_box = []

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_box.append(p.get("code", [""])[0])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Autorizado. Cierra esta ventana y vuelve al terminal.</h2>")
    def log_message(self, *a):
        pass

srv = http.server.HTTPServer(("127.0.0.1", 9085), H)
t = threading.Thread(target=srv.handle_request, daemon=True)
t.start()

url = ("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid,
    "redirect_uri": redir,
    "response_type": "code",
    "scope": scope,
    "access_type": "offline",
    "prompt": "consent",
}))

print()
print("Abriendo navegador para autorizar Gmail...")
webbrowser.open(url)
print("Esperando autorizacion...")
t.join(timeout=120)

if code_box and code_box[0]:
    code = code_box[0]
    print("Codigo recibido automaticamente.")
else:
    print()
    print("No se capturo el codigo automaticamente.")
    print("Copia el valor de 'code=' que aparece en la URL del navegador.")
    code = input("Pega el codigo aqui: ").strip()

data = urllib.parse.urlencode({
    "code": code,
    "client_id": cid,
    "client_secret": csec,
    "redirect_uri": redir,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
req.add_header("Content-Type", "application/x-www-form-urlencoded")

try:
    t2 = json.loads(urllib.request.urlopen(req).read())
    rt = t2.get("refresh_token", "")
    if rt:
        print()
        print("REFRESH TOKEN:")
        print(rt)
        print()
        print("Copia ese token y daselo a Claude.")
    else:
        print("ERROR - respuesta:", t2)
except Exception as e:
    print("ERROR:", e)
