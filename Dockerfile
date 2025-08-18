FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
#CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--worker-class", "aiohttp.worker.GunicornWebWorker", "app:app"]
CMD ["python", "start.py"]
EXPOSE 10000