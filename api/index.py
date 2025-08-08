
import sys
import os
# Add the parent directory
sys.path.append(os.path.abspath(".."))

import app
import y1 

from http.server import BaseHTTPRequestHandler
import re
import json
# Create a custom HTTP request handler
class handler(BaseHTTPRequestHandler):
	# Define how to handle GET requests
	def do_GET(self):
		print("Here => ", self.path)
		if self.path == "/":
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(
						"Python API Example s - Welcome to the homepage!".encode("utf-8")
				)
		elif self.path == "/params":
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(
						"PARAMs".encode("utf-8")
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
		if self.path in ["/params", "/params2"]:				
			try:
				foo1 = y1.foo2
				if self.path == "/params2":
					foo1 = y1.b1_foo2	
					
				# Set response headers
				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.send_header('Transfer-Encoding', 'chunked')  # Enable chunked transfer
				self.end_headers()				
				
				content_length = int(self.headers.get("Content-Length", 0))
				post_data = self.rfile.read(content_length).decode('utf-8')
				#print(post_data)
				if 0:				
					pattern = r'name="([^"]+)"\s*\r?\n\r?\n([^\r\n]+)'
					matches = re.findall(pattern, post_data)	
					form_dict = {name: value for name, value in matches}	
				else:
					form_dict = json.loads(post_data)
					#print(form_dict)
				data = form_dict
				bin_data = bytes.fromhex(data['bin'])
				no = int(data['no'], 16)
				mask = int(data['mask'], 16)
				#print(bin_data, no, mask)
				for i in range(50):
					new_bin, new_no, new_mask, ret = foo1(bin_data, no, mask)
					no = new_no+1
					mask = mask
					print(f"Iteration {i}: {new_no=:08x} {new_mask=:08x} {ret=}")
					if ret == 0:						
						json_data = {"result": "True", "bin": new_bin.hex(), "no": f"{new_no:08x}", "mask": f"{new_mask:08x}"}
					else:
						json_data = {"result": "False"}
					json_str = json.dumps(json_data) + "\n"  # NDJSON format
					
					encoded = json_str.encode('utf-8')
					# Write chunk size in hex, then the data, then CRLF
					self.wfile.write(f"{len(encoded):X}\r\n".encode('utf-8'))
					self.wfile.write(encoded)
					self.wfile.write(b"\r\n")
					self.wfile.flush()			
				# End of chunks
				self.wfile.write(b"0\r\n\r\n")
				self.wfile.flush()
			except BrokenPipeError:
				print("Client disconnected before response was complete.")
				# End of chunks
				self.wfile.write(b"0\r\n\r\n")
				self.wfile.flush()
				return
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
			error_data = {"message": f"Not Found{self.path}", "status": "error"}
			self.wfile.write(json.dumps(error_data).encode("utf-8"))
#async def handler (req):
#  app.handle_params(req)