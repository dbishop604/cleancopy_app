import os
import uuid
import redis
from rq import Queue
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from processor import process_file

# Flask app
app = Flask(__name__)

# Redis connection for RQ
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(redis_url)
q = Queue("default", connection=redis_conn)

# File storage
UPLOAD_FOLDER = "/data/uploads"
RESULTS_FOLDER = "/data/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    # Save file with unique name
    job_id = str(uuid.uuid4())
    filename = secure_filename(job_id + "_" + file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Enqueue background job
    job = q.enqueue(process_file, file_path, job_id, job_timeout="10m")

    return render_template("processing.html", task_id=job.get_id())

@app.route("/status/<job_id>")
def job_status(job_id):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        if job.is_finished:
            return jsonify({"status": "done", "result": job.result})
        elif job.is_failed:
            return jsonify({"status": "error", "message": str(job.exc_info)})
        else:
            return jsonify({"status": "processing"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Job fetch failed: {str(e)}"})

@app.route("/download/<job_id>")
def download_file(job_id):
    output_path = os.path.join(RESULTS_FOLDER, f"{job_id}.docx")
    if not os.path.exists(output_path):
        return "File not found or not ready yet", 404
    return send_file(output_path, as_attachment=True)

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/healthz")
def healthz():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
