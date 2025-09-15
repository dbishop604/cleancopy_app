import os
import redis
from rq import Queue
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from worker import process_file_job

app = Flask(__name__)
CORS(app)

# Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

# Health check
@app.route("/healthz")
def health_check():
    return "OK", 200

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Upload + queue file for processing
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    upload_folder = "/data/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"status": "queued", "job_id": job.get_id()})

# Check job status
@app.route("/status/<job_id>")
def job_status(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        if job.is_finished:
            return jsonify({"status": "finished", "result": job.result})
        elif job.is_failed:
            return jsonify({"status": "failed", "message": str(job.exc_info)})
        else:
            return jsonify({"status": "queued"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Download processed file
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory("/data/output", filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
