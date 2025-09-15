# ---------------- app.py ----------------
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_session import Session
import os
from rq import Queue
from redis import Redis
from worker import process_file_job
import uuid

app = Flask(__name__)
CORS(app)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Redis Connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

UPLOAD_FOLDER = '/data/uploads'
OUTPUT_FOLDER = '/data/output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/healthz")
def health():
    return "OK", 200

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part", "status": "error"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file", "status": "error"}), 400

    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{file.filename}")
    file.save(file_path)

    job = queue.enqueue(process_file_job, file_path, OUTPUT_FOLDER, job_id, job_id=job_id)
    return jsonify({"job_id": job.get_id(), "status": "queued"})

@app.route("/status/<job_id>")
def get_status(job_id):
    job = queue.fetch_job(job_id)
    if not job:
        return jsonify({"message": "Invalid job ID", "status": "error"}), 404
    return jsonify({"job_id": job.get_id(), "status": job.get_status()})

@app.route("/result/<job_id>")
def get_result(job_id):
    result_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.docx")
    if os.path.exists(result_path):
        return send_file(result_path, as_attachment=True)
    return jsonify({"message": "Result not ready", "status": "error"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
