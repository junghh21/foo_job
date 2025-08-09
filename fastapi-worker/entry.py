# entry.py
from fastapi import serve
from app import app

def on_fetch(request):
	return serve(app, request)
