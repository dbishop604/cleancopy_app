import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_session import Session
import redis
from rq import Queue
from worker import process_file_job

app = Flask(__name__)
CORS(app)

# Setup session
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

# Log to confirm Redis connection
try:
    redis_conn.ping()
    print("✅ Successfully connected to Redis at:", redis_url)
except Exception as e:
    print("❌ Failed to connect to Redis:", e)

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
def healthz():
    return "OK", 200

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"job_id": job.get_id()}), 202

@app.route("/result/<job_id>", methods=["GET"])
def get_result(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "message": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
