
import sys
import os
# Add the parent directory
sys.path.append(os.path.abspath(".."))

import app
import y1 

from http.server import BaseHTTPRequestHandler
import json
# Create a custom HTTP request handler
class handler(BaseHTTPRequestHandler):
	# Define how to handle GET requests
	def do_GET(self):
		print("Here => ", self.path)
		if self.path == "/api":
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(
						"Python API Example - Welcome to the homepage!".encode("utf-8")
				)
		else:
				self.send_response(404)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				error_data = {"message": "Not Found", "status": "error"}
				json_error_data = json.dumps(error_data)
				self.wfile.write(json_error_data.encode("utf-8"))
				
	def do_POST(self):
		print("POST =>", self.path)
		if self.path in ["/api/params", "/api/params2"]:
			foo1 = y1.foo2
			if self.path == "/api/params2":
				foo1 = y1.b1_foo2
			content_length = int(self.headers.get("Content-Length", 0))
			post_data = self.rfile.read(content_length)
			try:
				data = json.loads(post_data)
				bin_data = bytes.fromhex(data['bin'])
				no = int(data['no'], 16)
				mask = int(data['mask'], 16)
				
				json_data = {"result": "False"}
				for i in range(30):
					new_bin, new_no, new_mask, ret = foo1(bin_data, no, mask)
					no = new_no+1
					mask = mask
					if ret == 0:
						json_data = {"result": "True", "bin": new_bin.hex(), "no": f"{new_no:08x}", "mask": f"{new_mask:08x}"}
						print(f"Iteration {i}: {new_no=:08x} {new_mask=:08x} {ret=}")
						break									

				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				self.wfile.write(json.dumps(json_data).encode("utf-8"))
			except json.JSONDecodeError:
				self.send_response(400)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				error_data = {"status": "error", "message": "Invalid JSON"}
				self.wfile.write(json.dumps(error_data).encode("utf-8"))
		else:
			self.send_response(404)
			self.send_header("Content-type", "application/json")
			self.end_headers()
			error_data = {"message": "Not Found", "status": "error"}
			self.wfile.write(json.dumps(error_data).encode("utf-8"))
#async def handler (req):
#  app.handle_params(req)