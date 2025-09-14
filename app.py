import os
import uuid
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_file
)
from werkzeug.utils import secure_filename
from redis import Redis
from rq import Queue
from rq.job import Job
from worker import process_file_job

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Redis setup ---
redis_url = os.environ.get("REDIS_URL")
redis_conn = Redis.from_url(redis_url) if redis_url else None
q = Queue("default", connection=redis_conn) if redis_conn else None


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/success/<job_id>")
def success(job_id):
    return render_template("success.html", job_id=job_id)


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


@app.route("/coffee")
def coffee():
    return render_template("coffee.html")


@app.route("/convert", methods=["POST"])
def convert():
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of service and privacy policy before uploading.")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    job_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.docx")

    f.save(input_path)

    if not redis_conn:
        return jsonify({"status": "error", "message": "Redis is not connected."}), 500

    job = q.enqueue(process_file_job, input_path, output_path, job_id=job_id)
    return redirect(url_for("success", job_id=job.get_id()))


@app.route("/status/<task_id>")
def status(task_id):
    if not q:
        return jsonify({"status": "error", "message": "Redis is not connected."})
    try:
        job = q.fetch_job(task_id)
        if not job:
            return jsonify({"status": "error", "message": "Job not found"})
        if job.is_finished:
            return jsonify({"status": "done"})
        elif job.is_failed:
            return jsonify({"status": "error", "message": str(job.exc_info)})
        else:
            return jsonify({"status": "processing"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/download/<task_id>")
def download(task_id):
    output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}.docx")
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return "File not found", 404


@app.route("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
