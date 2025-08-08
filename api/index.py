
import sys
import os
# Add the parent directory
sys.path.append(os.path.abspath(".."))
import traceback

#import app
import y1

from flask import Flask, request, stream_with_context, Response
import json
app = Flask(__name__)

from multiprocessing import Process, shared_memory, Semaphore
import struct

def add_instance ():
	'''
	try:
		shm = shared_memory.SharedMemory("foo_shm")
	except:
		shm = shared_memory.SharedMemory("foo_shm", create=True, size=8)
	
	cur = struct.unpack('i', shm.buf[:4])[0] 
	cur += 1
	shm.buf[:4] = struct.pack('i', cur)
	return cur
	'''
	try:
		ex_cnt = int(os.environ.get('EX_CNT', '0')) + 1
	except:
		ex_cnt = 1
	os.environ['EX_CNT'] = f"{ex_cnt}"
	return 0
	
def get_cur_instance ():
	'''
	try:
		shm = shared_memory.SharedMemory("foo_shm")
	except:
		shm = shared_memory.SharedMemory("foo_shm", create=True, size=8)
	cur = struct.unpack('i', shm.buf[:4])[0]
	return cur
	'''
	try:
		ex_cnt = int(os.environ.get('EX_CNT', '0'))
	except:
		ex_cnt = 0
	return ex_cnt

@app.route("/")
def home():
	return "Hello from Flask on Vercel!"

# request.method,               # GET or POST
# request.url,                     # Full URL including query string
# request.base_url,           # URL without query string
# request.path,                   # Path portion (e.g. /example)
# request.full_path,         # Path + query string
# request.host_url,           # Host (e.g. http://127.0.0.1:5000/)
# request.url_root,           # Root URL (host + script root)
# request.args.to_dict()          # Query parameters as dict

@app.route('/params', methods=['POST'])
@app.route('/params2', methods=['POST'])
def params():
	@stream_with_context
	def generate():
		my_cnt = add_instance()
		try:
			data = request.get_json()
			#print(data)
			foo1 = y1.foo2
			if request.path == "/params2":
				foo1 = y1.b1_foo2
			bin_data = bytes.fromhex(data['bin'])
			no = int(data['no'], 16)
			mask = int(data['mask'], 16)
			#print(bin_data, no, mask)
			for i in range(50):
				if get_cur_instance() != my_cnt:
					json_data = {"result": "False"}
					print(f'X == {my_cnt}')
					return json.dumps(json_data) + "\n"  # NDJSON format
				new_bin, new_no, new_mask, ret = foo1(bin_data, no, mask)
				no = new_no+1
				mask = mask
				print(f"Iteration {i}: {new_no=:08x} {new_mask=:08x} {ret=}")
				if ret == 0:
					json_data = {"result": "True", "bin": new_bin.hex(), "no": f"{new_no:08x}", "mask": f"{new_mask:08x}"}
					return json.dumps(json_data) + "\n"  # NDJSON format					
				else:
					json_data = {"result": "False"}
					#yield json.dumps(json_data) + "\n"  # NDJSON format
					pass
			json_data = {"result": "False"}
			return json.dumps(json_data) + "\n"  # NDJSON format
		except Exception as e:
			print("Error:", e)
			traceback.print_exc()	
	return Response(generate(), mimetype='application/x-ndjson')
