import urllib.parse, urllib.request, json, webbrowser, http.server, threading, sys

cid = input("Client ID: ")
csec = input("Client Secret: ")
redir = "http://127.0.0.1:8085/callback"
scope = "https://www.googleapis.com/auth/gmail.readonly"
code_box = []

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_box.append(p.get("code", [" "])[0])
        self.send_response(200); self.end_headers()
        self.wfile.write(b"OK cierra esta ventana")
    def log_message(self, *a): pass

threading.Thread(target=http.server.HTTPServer(("127.0.0.1", 8085), H).handle_request, daemon=True).start()
url = ("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": redir, "response_type": "code",
    "scope": scope, "access_type": "offline", "prompt": "consent"}))
print("Abriendo navegador...")
webbrowser.open(url)
input("Pulsa ENTER tras autorizar en el navegador...")
code = code_box[0] if code_box else input("Pega el code= de la URL: ")
data = urllib.parse.urlencode({"code": code, "client_id": cid, "client_secret": csec,
    "redirect_uri": redir, "grant_type": "authorization_code"}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
req.add_header("Content-Type", "application/x-www-form-urlencoded")
t = json.loads(urllib.request.urlopen(req).read())
print("REFRESH TOKEN:", t.get("refresh_token", "ERROR: " + str(t)))
