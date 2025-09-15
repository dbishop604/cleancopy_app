# app.py
import os
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_session import Session
from rq import Queue
from worker import process_file_job as process_file

app = Flask(__name__)
CORS(app)

# Ensure REDIS_URL is set
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

# Connect to Redis
r = redis.Redis.from_url(redis_url)
q = Queue(connection=r)

@app.route("/healthz")
def health():
    try:
        r.ping()
        return jsonify({"status": "ok"})
    except redis.exceptions.ConnectionError:
        return jsonify({"status": "error", "message": "Redis is not connected"}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})

    save_path = os.path.join("/data/uploads", file.filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)

    job = q.enqueue(process_file, save_path)
    return jsonify({"status": "queued", "job_id": job.get_id()})

@app.route("/result/<job_id>")
def get_result(job_id):
    job = q.fetch_job(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"})
    if job.is_finished:
        return jsonify({"status": "done", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "message": str(job.exc_info)})
    else:
        return jsonify({"status": "pending"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# worker.py
import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

# Ensure REDIS_URL is set
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment var
