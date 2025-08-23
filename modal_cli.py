import modal
import time
import random

# Reference the deployed function
p = modal.Function.from_name("example-basic-web1", "p")
f = modal.Function.from_name("example-basic-web1", "f")

while True:
	p.remote()
	for i in range(6):
		print(f.remote(i))
		time.sleep(random.randint(30, 60))
	
