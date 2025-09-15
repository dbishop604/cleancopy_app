import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import redis
from rq import Queue
from worker import process_file_job as process_file  # ensure worker.py has this

# Flask setup
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/data/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
r = redis.from_url(redis_url)
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
        "message": "File uploaded and queued for processing."
    })

@app.route("/results/<job_id>", methods=["GET"])
def get_results(job_id):
    job = q.fetch_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})

@app.route("/healthz")
def healthz():
    try:
        r.ping()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
