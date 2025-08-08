
import sys
import os
# Add the parent directory
sys.path.append(os.path.abspath(".."))

import app

from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        
#async def handler (req):
#  app.handle_params(req)