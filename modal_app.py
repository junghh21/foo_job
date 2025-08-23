
"""
import subprocess
import modal
# Vẫn tạo image có CUDA + Python
image = (
		modal.Image.from_registry("nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.11")
				.pip_install("cupy-cuda12x"))
# 1) Cập nhật gói và cài git + curl + gnupg\n
subprocess.run(["apt-get", "update", "-y"], check=True)
subprocess.run(["apt-get", "install", "-y", "git", "curl", "gnupg"], check=True)
# 2) Cài Node.js (LTS 18)\n
subprocess.run(
		"curl -fsSL https://deb.nodesource.com/setup_18.x | bash -",
				shell=True,
				check=True)
subprocess.run(["apt-get", "install", "-y", "nodejs"], check=True)
# 3) Clone repo
subprocess.run(["git", "clone", "https://github.com/vudeptrai79016-wq/tool.git"], check=False)
# 4) Chạy node app.js và giữ tiến trình
process = subprocess.Popen(
		["node", "app.js"],
				cwd="tool")
process.wait()
"""
import subprocess
import modal
import time
import random

image = (
		modal.Image.debian_slim(python_version="3.10")
		.apt_install("procps", "git", "coreutils")
		#modal.Image.from_registry("ubuntu:22.04", add_python="3.10")
		#.apt_install("git")
		.pip_install("aiohttp", "psutil", "requests")
		.add_local_dir("./", "/root/app", copy=True)
		.run_commands(
			"chdir /root/app",
			#"ls -al /root/app",
			#"python3 /root/app/start.py"
		)
)
app = modal.App(name="example-basic-web1", image=image)

pid = None
@app.function()
def p():
	global pid
	if pid:
		return
	import os, sys
	import time
	import importlib.util
	import psutil
	pid = os.fork()
	if pid == 0:
		os.chdir('/root/app')
		sys.path.append('/root/app')
		print("Current working directory:", os.getcwd())
		#directory = './'
		#files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
		#print(files)

		from app import foo_runner, websocket_client
		#print(dir(app))
		import asyncio
		info = {}
		async def aa_start():
			with open("brg_url.txt") as f:
				ws_url = f.readline()
			cores = psutil.cpu_count(logical=False)
			#cores = 4
			info['tasks'] = []
			for i in range(cores):
				q = asyncio.Queue()
				runner = asyncio.create_task(foo_runner(i, q))
				ws = asyncio.create_task(websocket_client(i, q, ws_url))
				info['tasks'].append(runner)
				info['tasks'].append(ws)
		async def aa_stop():
			global pid
			for task in info['tasks']:
				task.cancel()
				try:
					await task
				except asyncio.CancelledError:
					pass
					#print("Background task cancelled.")
			
		async def aa_main():
			print("Starting task...")
			await aa_start()
			await asyncio.sleep(random.randint(120, 180))
			#await asyncio.sleep(30)
			await aa_stop()
			print("Task complete!")
		asyncio.run(aa_main())
		#exit()
		import subprocess
		result = subprocess.run(
				["ps", "-eo", "pid,comm"],
				capture_output=True,
				text=True  # Automatically decodes bytes to string
		)
		#print(result.stdout)
		import signal
		os.kill(pid, signal.SIGTERM)
	else:
		print("Parent process, child PID:", pid)
		time.sleep(1)

@app.function()
def f(i):
	import requests
	url = "https://data-api.coindesk.com/index/cc/v1/latest/tick?market=cadli&instruments=BTC-USD&apply_mapping=true&groups=VALUE"
	try:
		response = requests.get(url)
		data = response.json()
		price = data['Data']['BTC-USD']['VALUE']
		return f"Current Bitcoin price: ${price}"
	except:
		return "Unexpected Error Occurred!!"


@app.local_entrypoint()
def main():
	while True:
		p.remote()
		for i in range(6):
			print(f.remote(i))
			time.sleep(random.randint(30, 60))
		


