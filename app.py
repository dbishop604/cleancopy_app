import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import redis
from rq import Queue
from worker import process_file_job

app = Flask(__name__)
CORS(app)

# Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

redis_conn = redis.from_url(redis_url, decode_responses=True)
queue = Queue(connection=redis_conn)

# Test Redis connection on startup
try:
    redis_conn.ping()
    print("✅ Connected to Redis successfully")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    raise

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    upload_folder = "/data/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    # Queue background job
    job = queue.enqueue(process_file_job, file_path)
    return jsonify({"job_id": job.get_id(), "status": "queued"})

@app.route("/result/<job_id>", methods=["GET"])
def get_result(job_id):
    job = queue.fetch_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)})
    else:
        return jsonify({"status": job.get_status()})

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    output_folder = "/data/output"
    return send_from_directory(output_folder, filename, as_attachment=True)

@app.route("/healthz")
def health_check():
    try:
        redis_conn.ping()
        return jsonify({"status": "ok", "message": "Healthy"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
