import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import redis
from rq import Queue
from worker import process_file_job as process_file  # or change to processor if needed

# Flask app setup
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/data/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r = redis.Redis.from_url(redis_url)
    r.ping()  # test connection
    q = Queue(connection=r)
    print(f"✅ Connected to Redis at: {redis_url}")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    r = None
    q = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if not q:
        return jsonify({"status": "error", "message": "Redis is not connected"}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    file_path = os.pat_
