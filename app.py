import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import redis
from rq import Queue
from worker import process_file

# Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/data/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Redis connection (use REDIS_URL from Render/Upstash)
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

    job = q.enqueue(process_file, file_path)

    return jsonify({
        "job_id": job.id,
        "message": "File uploaded and job queued"
    })

@app.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed"})
    else:
        return jsonify({"status": "in_progress"})

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/healthz", methods=["GET"])
def health_check():
    try:
        r.ping()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
