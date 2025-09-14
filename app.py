import os
import io
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, jsonify
)
from werkzeug.utils import secure_filename
from redis import Redis
from rq import Queue
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

# Shared disk (must match render.yaml)
BASE_FOLDER = "/app/data"
UPLOAD_FOLDER = os.path.join(BASE_FOLDER, "uploads")
CONVERTED_FOLDER = os.path.join(BASE_FOLDER, "converted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# --- Redis queue connection ---
redis_url = os.environ.get("REDIS_URL")
redis_conn = Redis.from_url(redis_url) if redis_url else None
q = Queue(connection=redis_conn) if redis_conn else None

# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html", plan="free")

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

    if not redis_conn or not q:
        return jsonify({"status": "error", "message": "Redis is not connected. Please try again shortly."}), 500

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(upload_path)

    fmt = request.form.get("format", "docx")
    output_filename = filename.rsplit(".", 1)[0] + f".{fmt}"
    output_path = os.path.join(CONVERTED_FOLDER, output_filename)

    # Queue background job (runs in worker.py)
    job = q.enqueue("worker.process_file_job", upload_path, fmt, output_filename)

    return redirect(url_for("success", job_id=job.get_id()))

@app.route("/status/<job_id>")
def status(job_id):
    if not redis_conn:
        return jsonify({"status": "error", "message": "Redis not available"}), 500

    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 404

    if job.is_finished:
        return jsonify({
            "status": "finished",
            "download_url": url_for("download_file", filename=job.result["output"].split("/")[-1])
        })
    elif job.is_failed:
        return jsonify({"status": "error", "message": str(job.exc_info)})
    else:
        return jsonify({"status": "pending"})

@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(CONVERTED_FOLDER, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)

# --- Health check for Render ---
@app.route("/healthz")
def healthz():
    return "OK", 200

# --- Local run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
