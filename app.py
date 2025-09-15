import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from redis import Redis
from rq import Queue
from worker import process_file_job

UPLOAD_FOLDER = "/data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Redis connection from environment
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("❌ REDIS_URL environment variable is not set. Please configure it in Render.")

try:
    redis_conn = Redis.from_url(redis_url)
    redis_conn.ping()
except Exception as e:
    raise RuntimeError(f"❌ Could not connect to Redis. Error: {e}")

# Create the default RQ queue
queue = Queue("default", connection=redis_conn)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Enqueue the file processing job
    job = queue.enqueue(process_file_job, filepath)

    return jsonify({"status": "success", "job_id": job.get_id()})


@app.route("/progress/<job_id>")
def job_status(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return jsonify({"status": "error", "message": "Job not found"}), 404

    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "message": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})


@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "File not found"}), 404
    return send_file(file_path, as_attachment=True)


@app.route("/healthz")
def health_check():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
