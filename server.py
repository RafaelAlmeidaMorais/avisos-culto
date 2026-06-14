#!/usr/bin/env python3
# Aviso de veículo - overlay online para ProPresenter
# Overlay:  https://seu-dominio/
# Controle: https://seu-dominio/control?key=SUA_SENHA

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from urllib.parse import urlparse, parse_qs

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8787"))
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

STATE = {
    "visible": False,
    "veiculo": "",
    "cor": "",
    "placa": "",
    "mensagem": "Favor comparecer ao estacionamento",
}

OVERLAY_HTML = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Aviso de Veículo - Overlay</title>
<style>
  :root {
    --card: rgba(16,16,16,.92);
    --text: #ffffff;
    --muted: rgba(255,255,255,.75);
    --line: rgba(255,255,255,.16);
    --accent: #ff8a00;
  }
  html, body {
    margin: 0; width: 100%; height: 100%; overflow: hidden; background: transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: var(--text);
  }
  .stage { position: fixed; inset: 0; display: grid; place-items: end center; padding: 0 6vw 6vh; box-sizing: border-box; opacity: 0; transform: translateY(28px); transition: opacity .25s ease, transform .25s ease; }
  .stage.show { opacity: 1; transform: translateY(0); }
  .alert { width: min(1500px, 88vw); min-height: 210px; background: var(--card); border: 2px solid var(--line); border-left: 16px solid var(--accent); box-shadow: 0 28px 80px rgba(0,0,0,.45); border-radius: 28px; padding: 34px 44px 38px; box-sizing: border-box; }
  .headline { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
  .badge { background: var(--accent); color: #111; font-weight: 900; letter-spacing: .06em; font-size: clamp(28px, 3.2vw, 54px); line-height: 1; padding: 16px 22px; border-radius: 16px; }
  .message { font-size: clamp(26px, 2.2vw, 44px); font-weight: 700; color: var(--text); line-height: 1.1; }
  .fields { display: grid; grid-template-columns: 1.15fr .75fr .85fr; gap: 18px; }
  .field { border: 1px solid var(--line); border-radius: 18px; padding: 18px 22px; background: rgba(255,255,255,.055); min-width: 0; }
  .label { color: var(--muted); font-size: clamp(16px, 1.2vw, 24px); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
  .value { font-size: clamp(32px, 3vw, 62px); font-weight: 900; line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  @media (max-width: 900px) { .fields { grid-template-columns: 1fr; } .alert { min-height: auto; } }
</style>
</head>
<body>
  <div id="stage" class="stage">
    <section class="alert">
      <div class="headline">
        <div class="badge">ATENÇÃO</div>
        <div id="mensagem" class="message">Favor comparecer ao estacionamento</div>
      </div>
      <div class="fields">
        <div class="field"><div class="label">Veículo</div><div id="veiculo" class="value">—</div></div>
        <div class="field"><div class="label">Cor</div><div id="cor" class="value">—</div></div>
        <div class="field"><div class="label">Placa</div><div id="placa" class="value">—</div></div>
      </div>
    </section>
  </div>
<script>
async function loadState() {
  try {
    const r = await fetch('/api/state', {cache: 'no-store'});
    const s = await r.json();
    document.getElementById('stage').classList.toggle('show', !!s.visible);
    document.getElementById('mensagem').textContent = s.mensagem || 'Favor comparecer ao estacionamento';
    document.getElementById('veiculo').textContent = s.veiculo || '—';
    document.getElementById('cor').textContent = s.cor || '—';
    document.getElementById('placa').textContent = s.placa || '—';
  } catch(e) {}
}
loadState();
setInterval(loadState, 500);
</script>
</body>
</html>'''

CONTROL_HTML = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Controle - Aviso de Veículo</title>
<style>
  body { margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; background:#111; color:#fff; }
  main { max-width: 760px; margin: 0 auto; padding: 36px 22px; }
  h1 { margin: 0 0 8px; font-size: 32px; }
  p { color: rgba(255,255,255,.72); margin: 0 0 26px; }
  label { display:block; font-weight: 800; margin: 18px 0 8px; }
  input { width:100%; box-sizing:border-box; border:1px solid rgba(255,255,255,.18); background:#1d1d1d; color:#fff; font-size:24px; padding:16px 18px; border-radius:12px; outline:none; }
  input:focus { border-color:#ff8a00; }
  .row { display:grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  button { border:0; border-radius:12px; padding:16px 18px; margin-top:20px; font-size:20px; font-weight:900; cursor:pointer; }
  .show { background:#ff8a00; color:#111; }
  .clear { background:#333; color:#fff; }
  .status { margin-top:22px; color:#9fe29f; font-weight:700; min-height:24px; }
  a { color:#ffb15c; }
</style>
</head>
<body>
<main>
  <h1>Aviso de veículo</h1>
  <p>Overlay: <a href="/" target="_blank">abrir tela de exibição</a></p>

  <label for="mensagem">Mensagem</label>
  <input id="mensagem" value="Favor comparecer ao estacionamento" />

  <label for="veiculo">Veículo</label>
  <input id="veiculo" placeholder="Ex.: Toyota Corolla" />

  <div class="row">
    <div><label for="cor">Cor</label><input id="cor" placeholder="Ex.: Prata" /></div>
    <div><label for="placa">Placa</label><input id="placa" placeholder="Ex.: ABC1D23" /></div>
  </div>

  <div class="row">
    <button class="show" onclick="showAlert()">Mostrar aviso</button>
    <button class="clear" onclick="clearAlert()">Limpar / ocultar</button>
  </div>
  <div id="status" class="status"></div>
</main>
<script>
const params = new URLSearchParams(window.location.search);
const key = params.get('key') || '';
function api(path) { return key ? `${path}?key=${encodeURIComponent(key)}` : path; }
async function post(url, data) {
  const r = await fetch(api(url), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data || {}) });
  if (!r.ok) throw new Error('Falha ao atualizar. Verifique a senha/key.');
  return await r.json();
}
function values(visible) {
  return {
    visible,
    mensagem: document.getElementById('mensagem').value.trim(),
    veiculo: document.getElementById('veiculo').value.trim(),
    cor: document.getElementById('cor').value.trim(),
    placa: document.getElementById('placa').value.trim(),
  };
}
async function showAlert() {
  try { await post('/api/update', values(true)); document.getElementById('status').textContent = 'Aviso exibido.'; }
  catch(e) { document.getElementById('status').textContent = e.message; }
}
async function clearAlert() {
  try { await post('/api/clear', {}); document.getElementById('status').textContent = 'Aviso ocultado.'; }
  catch(e) { document.getElementById('status').textContent = e.message; }
}
async function load() {
  try {
    const s = await (await fetch('/api/state', {cache:'no-store'})).json();
    ['mensagem','veiculo','cor','placa'].forEach(k => { if (s[k]) document.getElementById(k).value = s[k]; });
  } catch(e) {}
}
load();
</script>
</body>
</html>'''

LOGIN_HTML = r'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Acesso</title><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#111;color:white;margin:0;display:grid;place-items:center;min-height:100vh}main{width:min(92vw,480px)}input,button{width:100%;box-sizing:border-box;font-size:22px;padding:16px;border-radius:12px;border:0;margin-top:12px}button{font-weight:900;background:#ff8a00;color:#111}</style></head><body><main><h1>Acesso ao controle</h1><p>Digite a senha/key do painel.</p><input id="key" type="password" autofocus><button onclick="location.href='/control?key='+encodeURIComponent(document.getElementById('key').value)">Entrar</button></main></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def _send(self, status=200, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _authorized(self):
        if not ADMIN_KEY:
            return True
        q = parse_qs(urlparse(self.path).query)
        supplied = (q.get("key") or [""])[0] or self.headers.get("X-Admin-Key", "")
        return supplied == ADMIN_KEY

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/overlay":
            self._send(200, "text/html; charset=utf-8")
            self.wfile.write(OVERLAY_HTML.encode("utf-8"))
        elif path == "/control":
            if not self._authorized():
                self._send(200, "text/html; charset=utf-8")
                self.wfile.write(LOGIN_HTML.encode("utf-8"))
                return
            self._send(200, "text/html; charset=utf-8")
            self.wfile.write(CONTROL_HTML.encode("utf-8"))
        elif path == "/api/state":
            self._send(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps(STATE, ensure_ascii=False).encode("utf-8"))
        else:
            self._send(404)
            self.wfile.write(b"Not found")

    def do_POST(self):
        global STATE
        path = urlparse(self.path).path
        if not self._authorized():
            self._send(403, "application/json; charset=utf-8")
            self.wfile.write(json.dumps({"ok": False, "error": "unauthorized"}).encode("utf-8"))
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = {}
        if path == "/api/update":
            for k in ["visible", "veiculo", "cor", "placa", "mensagem"]:
                if k in data:
                    STATE[k] = data[k]
            self._send(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps({"ok": True, "state": STATE}, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/clear":
            STATE["visible"] = False
            self._send(200, "application/json; charset=utf-8")
            self.wfile.write(json.dumps({"ok": True, "state": STATE}, ensure_ascii=False).encode("utf-8"))
        else:
            self._send(404)
            self.wfile.write(b"Not found")

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    print(f"Aviso de veículo rodando na porta {PORT}")
    print("Controle: /control?key=SUA_SENHA")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
