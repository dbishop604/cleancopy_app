import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
from rq import Queue
import redis
import uuid

from worker import process_file_job

app = Flask(__name__)
CORS(app)

# Configure session (if needed for future)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Upload and output folder paths
UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Setup Redis Queue connection
redis_url = os.getenv("REDIS_URL")

# 🧪 Redis connection test (log to console on startup)
try:
    test_conn = redis.from_url(redis_url)
    test_conn.ping()
    print("✅ Redis connected successfully.")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")

# Use redis.from_url to connect Redis client and queue
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    saved_filename = f"{unique_id}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
    file.save(file_path)

    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"job_id": job.get_id()}), 202

@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = queue.fetch_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc
