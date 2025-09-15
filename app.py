import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rq import Queue
import redis
from worker import process_file_job

# Setup
app = Flask(__name__)
CORS(app)

# Redis setup
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "SeamlessDocs OCR is running."

@app.route("/healthz")
def health_check():
    return jsonify({"status": "healthy"})

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Enqueue job
    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"status": "queued", "job_id": job.get_id()})

@app.route("/status/<job_id>")
def check_status(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        if job.is_finished:
            return jsonify({"status": "finished", "result": job.result})
        elif job.is_failed:
            return jsonify({"status": "failed", "error": str(job.exc_info)})
        else:
            return jsonify({"status": "in progress"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/download/<filename>")
def downloa
