import modal
import time
import random

# Reference the deployed function
f = modal.Function.from_name("example-basic-web1", "f")

while True:
	for i in range(200):
		print(f.remote(i))
		time.sleep(random.randint(7, 14))
	time.sleep(900)
