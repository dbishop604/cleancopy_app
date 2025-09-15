import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import redis
from rq import Queue
from worker import process_file_job as process_file

# Flask setup
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/data/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Redis setup
redis_url = os.getenv("REDIS_URL")
try:
    r = redis.Redis.from_url(redis_url)
    r.ping()  # Force connection test
    q = Queue(connection=r)
except Exception as e:
    r = None
    q = None
    print("❌ Redis connection failed:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
def health():
    return jsonify({"status": "ok"})

@app.route("/upload", methods=["POST"])
def upload_file():
    if not q:
        return jsonify({"message": "Redis is not connected", "status": "error"}), 500

    if "file" not in request.files:
        return jsonify({"message": "No file part", "status": "error"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No file selected", "status": "error"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    job = q.enqueue(process_file, file_path)

    return jsonify({
        "job_id": job.id,
        "message": "File uploaded and processing started",
        "status": "success"
    })
