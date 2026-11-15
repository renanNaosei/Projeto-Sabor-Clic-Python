"""Servidor do front-end para desenvolvimento: igual ao `python -m http.server`,
mas manda o navegador NUNCA guardar arquivos em cache (evita ver JS/CSS antigos)."""
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
PASTA = os.path.dirname(os.path.abspath(__file__))


class SemCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), partial(SemCache, directory=PASTA))
    print(f"Front-end em http://127.0.0.1:{PORTA}  (servindo {PASTA}, sem cache)")
    servidor.serve_forever()