#!/usr/bin/env python3
"""
Buwemon lokaler Server
Doppelklick auf diese Datei (oder: python3 server.py im Terminal)
Dann im Browser öffnen: http://localhost:8765
"""
import http.server, webbrowser, os, threading

PORT = 8765
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # silent

print(f"Buwemon läuft auf http://100.83.54.64:{PORT}")
print("Browser öffnet sich automatisch...")
print("Zum Beenden: Fenster schließen oder Strg+C")

def open_browser():
    import time; time.sleep(0.5)
    webbrowser.open(f'http://100.83.54.64:{PORT}/buwemon.html')

threading.Thread(target=open_browser, daemon=True).start()
http.server.HTTPServer(('', PORT), Handler).serve_forever()
