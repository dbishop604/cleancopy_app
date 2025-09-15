# app.py
import os
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_session import Session
from rq import Queue
import redis
from worker import process_file_job

app = Flask(__name__)
CORS(app)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Redis
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
    return render_template("index.html")

@app.route("/healthz")
def health():
    return "ok"

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"job_id": job.get_id()})

@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed"})
    else:
        return jsonify({"status": "processing"})

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
