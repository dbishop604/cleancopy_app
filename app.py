import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import redis
from rq import Queue
from worker import process_file_job as process_file  # Adjust if your function lives in processor.py

# Flask app setup
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/data/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(redis_url)
q = Queue(connection=r)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Queue the job
    job = q.enqueue(process_file, file_path)

    return jsonify({
        "job_id": job.id,
        "message": "File uploaded a
