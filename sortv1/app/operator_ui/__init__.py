"""Read-only local UI. No actuator or rearm endpoints."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
PAGE='''<!doctype html><html lang="es"><meta charset="utf-8"><title>SorTV1</title>
<style>body{font:18px system-ui;max-width:900px;margin:2rem auto;background:#f3f5f8;color:#182632}table{width:100%;border-collapse:collapse}td{padding:.6rem;border-bottom:1px solid #ccc}h1{font-size:2.5rem}</style>
<h1 id="state">CONSULTANDO</h1><table id="fields"></table><p><a href="/export.csv">Exportar registros CSV</a></p>
<p>Retirar un objeto y conciliar requiere aislar potencia y registrar evidencia. El rearme es físico.</p>
<script>async function refresh(){try{const d=await(await fetch('/api/status')).json();document.getElementById('state').textContent=d.estado;const t=document.getElementById('fields');t.replaceChildren();for(const [k,v] of Object.entries(d)){if(k==='estado')continue;const r=t.insertRow();r.insertCell().textContent=k;r.insertCell().textContent=typeof v==='object'?JSON.stringify(v):String(v??'PENDIENTE')}}catch(e){document.getElementById('state').textContent='FALLO DE ENLACE UI'}}setInterval(refresh,1000);refresh()</script></html>'''

def create_server(service,port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/':payload=PAGE.encode();kind='text/html; charset=utf-8'
            elif self.path=='/api/status':payload=json.dumps(service.snapshot(),allow_nan=False).encode();kind='application/json'
            elif self.path=='/export.csv':
                path=service.root/'evidence/experiments/export.csv';service.journal.export_csv(path);payload=path.read_bytes();kind='text/csv'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
        def log_message(self,*args):pass
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
