import os
import redis
from flask import Flask, request, render_template, jsonify, send_file
from rq import Queue
from worker import process_file_job

app = Flask(__name__)

# -------------------
# Redis Setup
# -------------------
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise RuntimeError("❌ REDIS_URL is not set in environment variables")

try:
    redis_conn = redis.Redis.from_url(redis_url, ssl=True, ssl_cert_reqs=None)
    redis_conn.ping()
    print("✅ Connected to Redis!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    redis_conn = None

# Task queue
q = Queue(connection=redis_conn) if redis_conn else None


# -------------------
# Routes
# -------------------
@app.route("/")
def index():
    """Upload form page"""
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    """Handle file upload and queue processing"""
    if not redis_conn or not q:
        return jsonify({"status": "error", "message": "Redis is not connected"}), 500

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    upload_dir = "/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    job = q.enqueue(process_file_job, file_path)
    return jsonify({"job_id": job.id, "message": "File uploaded and job queued"})


@app.route("/status/<job_id>")
def status(job_id):
    """Check job status"""
    if not redis_conn or not q:
        return jsonify({"status": "error", "message": "Redis is not connected"}), 500

    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid Job ID"}), 404

    if job.is_finished:
        return jsonify({"status": "done", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "error", "message": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})


@app.route("/download/<job_id>")
def download(job_id):
    """Download processed file"""
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return "Invalid Job ID", 404

    if not job.is_finished or not job.result:
        return "File not ready", 404

    output_file = job.result
    if not os.path.exists(output_file):
        return "File missing", 404

    return send_file(output_file, as_attachment=True)


@app.route("/healthz")
def healthz():
    """Health check for Render"""
    return "OK", 200


# -------------------
# Run (local only)
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
