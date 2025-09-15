import os
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_session import Session
from rq import Queue
from worker import process_file_job as process_file

app = Flask(__name__)
CORS(app)

# Redis setup
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

r = redis.Redis.from_url(redis_url)
q = Queue(connection=r)

# Health check route
@app.route("/healthz")
def health():
    try:
        r.ping()
        return jsonify({"status": "ok"})
    except redis.exceptions.ConnectionError:
        return jsonify({"status": "error", "message": "Redis is not connected"}), 500

# Rest of your routes...
