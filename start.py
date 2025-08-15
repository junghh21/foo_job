
import os
import sys
import time
import subprocess
import random

if __name__ == '__main__':
	script_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(script_dir)
	print(f"Working directory set to: {os.getcwd()}")
	try:
		while True:
			try:
				print("Kill apps.")
				subprocess.run(["pkill", "-f", "python3 app.py --proxy"])
				time.sleep(2)
				result = subprocess.run(
								"ps aux | grep 'python3 app.py' | grep -v grep | wc -l",
								shell=True,
								capture_output=True,
								text=True
				)		
				count = int(result.stdout.strip())
				if count > 0:
					time.sleep(5)
					continue
				print(f"Number of 'python3 app.py' processes: {count}")
				# Fetch latest changes from origin
				subprocess.run(["git", "-C", "./", "fetch"])
				# Get local and remote HEAD commit hashes
				local = subprocess.check_output(["git", "-C", "./", "rev-parse", "HEAD"]).strip()
				remote = subprocess.check_output(["git", "-C", "./", "rev-parse", "@{u}"]).strip()
				if local != remote:
					print("📥 Updates available. Pulling...")
					subprocess.run(["git", "-C", "./", "pull"])
				else:
					print("✅ Already up to date.")
				
				new_proc = subprocess.Popen(['python3', 'app.py', '--proxy'])
				print(f"🔁 Restarting script... {new_proc.pid}")
			except subprocess.CalledProcessError as e:
				print(f"❌ Git command failed: {e}")
			except Exception as e:
				print(f"⚠️ Unexpected error: {e}")
    
			time.sleep(random.randint(60*4, 60*9))
    
	except KeyboardInterrupt:
		print("\n[Main] Program terminated by user.")
