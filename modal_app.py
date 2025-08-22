
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
		.apt_install("procps", "git")
		#modal.Image.from_registry("ubuntu:22.04", add_python="3.10")
		#.apt_install("git")
		.pip_install("aiohttp", "psutil")
		.add_local_dir("./", "/root/app", copy=True)
		.run_commands(
			"chdir /root/app", 
			"ls -al /root/app", 
			#"python3 /root/app/start.py",
			"setsid python3 /root/app/start.py &> /dev/null &"
		)
)
app = modal.App(name="example-basic-web1", image=image)

@app.function()
def f(i):
	print(i)
	return i

@app.local_entrypoint()
def main():
	while True:
		for i in range(200):
			print(f.remote(i))
			time.sleep(random.randint(7, 14))
		time.sleep(900)
