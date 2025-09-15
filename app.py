import os
import redis
from rq import Queue
from flask import Flask, request, jsonify, send_from_directory
from worker import process_file_job  # This is just for local import
from werkzeug.utils import secure_filename

# Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file uploaded", "status": "error"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No filename found", "status": "error"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    job = queue.enqueue("worker.process_file_job", filepath)
    return jsonify({"message": "File uploaded successfully", "job_id": job.id, "status": "queued"}), 202

@app.route("/result/<filename>", methods=["GET"])
def get_result(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(filepath):
        return send_from_directory(OUTPUT_FOLDER, filename)
    return jsonify({"message": "F
