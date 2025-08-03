import json
import ssl
from aiohttp import web
import os
import y1

async def handle(request: web.Request) -> web.Response:
	"""A simple handler that greets the user."""
	name = request.match_info.get('name', "Anonymous")
	text = f"Hello, {name}, from your secure aiohttp server!"
	return web.Response(text=text)

async def handle_file(request):
	data = await request.post()
	uploaded_file = data['file']  # 'file' is the name attribute in your HTML form
	filename = uploaded_file.filename
	content = uploaded_file.file.read()  # Read file content as bytes

	# Save the file locally
	with open(f'{filename}', 'wb') as f:
		f.write(content)

	return web.Response(text=f"Uploaded {filename} successfully!")
	
async def handle_params(request):
	data = await request.post()
	bin = bytes.fromhex(data['bin'])
	no = int(data['no'], 16)
	mask = int(data['mask'], 16)
	print(f"req_params: {bin.hex()[:8]} {no=:08x} {mask=:08x}")
	bin, no, mask, ret = y1.foo2(bin, no, mask)
	if ret == -1:
		print(f"dXXXXXXXXXXXXXX")
		json_data = {
			"result": "False",
		}
	else:
		print(f"{no=:08x} {mask=:08x} {ret} ")
		json_data = {
			"result": "True",
			"bin": 		bin.hex(),
			"no": 		f"{no:08x}",
			"mask": 	f"{mask:08x}",
		}
	return web.json_response(json_data)	


# --- Main Application Setup ---
app = web.Application()
app.add_routes([
	web.get('/', handle),
	web.post('/file', handle_file),
	web.post('/params', handle_params),
])
 
def main():
	"""Sets up the SSL context and runs the aiohttp application."""
	
	cert_file = 'cert.pem'
	key_file = 'key.pem'

	# --- SSL Context Setup ---
	# For a robust and secure server, it's recommended to use
	# ssl.create_default_context.
	# ssl.Purpose.CLIENT_AUTH means the context is for a server-side socket,
	# which will authenticate clients.
	ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
	ssl_context.check_hostname = False
	ssl_context.verify_mode = ssl.CERT_NONE
	# Load your server's certificate and private key.
	# In a production environment, you would use a certificate from a
	# trusted Certificate Authority (CA) like Let's Encrypt.
	try:
		ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
		print(f"Successfully loaded certificate from '{cert_file}' and key from '{key_file}'.")
	except FileNotFoundError:
		print("=" * 60)
		print(f"ERROR: Could not find '{cert_file}' or '{key_file}'.")
		print("You can generate a self-signed certificate for development with:")
		print('openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/CN=localhost"')
		print("=" * 60)
		return
	except ssl.SSLError as e:
		print(f"An SSL error occurred: {e}")
		print("Please ensure your certificate and key files are valid and match.")
		return

	

	# --- Run the application with HTTPS ---
	# Passing the `ssl_context` to `run_app` is what enables HTTPS.
	host = '0.0.0.0'
	port = 8001
	print(f"Starting secure server on https://{host}:{port}")
	#web.run_app(app, host=host, port=port, ssl_context=ssl_context)
	web.run_app(app, host=host, port=port)


if __name__ == '__main__':
	script_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(script_dir)
	main()
