
import sys
import os
# Add the parent directory
sys.path.append(os.path.abspath(".."))

import app

async def handler (req):
  app.handle_params(req)