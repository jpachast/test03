#!/usr/bin/env python3
"""
Simple HTTP Server con headers anti-caché
Para servir archivos de proyecto sin caché del navegador
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Handler que agrega headers anti-caché a todas las respuestas"""
    
    def end_headers(self):
        # Headers anti-caché
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Silenciar logs para no llenar la consola
        pass


def run(port=8000, directory='.'):
    os.chdir(directory)
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, NoCacheHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)
