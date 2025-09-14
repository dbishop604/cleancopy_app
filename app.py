import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from redis import Redis
from rq import Queue
from worker import process_file_job

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

# Shared disk paths (both web + worker use /data mount on Render)
UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Redis connection
redis_conn = Redis.from_url(os.environ["REDIS_URL"])
q = Queue(connection=redis_conn)

@app.route("/")
def index():
    return render_template("index.html", plan="free")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/cancel")
def cancel_page():
    return render_template("cancel.html")

@app.route("/coffee")
def coffee():
    return render_template("coffee.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms before uploading.")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{secure_filename(f.filename)}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.docx")

    f.save(input_path)

    job = q.enqueue(process_file_job, input_path, output_path, job_id)

    return jsonify({"job_id": job.get_id()})

@app.route("/status/<job_id>")
def status(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"status": "not_found"}), 404

    if job.is_finished:
        return jsonify({"status": "finished", "download_url": f"/download/{job_id}"})
    elif job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})

@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"status": "not_found"}), 404
    job.cancel()
    return jsonify({"status": "cancelled"})

@app.route("/download/<job_id>")
def download(job_id):
    output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.docx")
    if not os.path.exists(output_path):
        return jsonify({"error": "File not ready"}), 404
    return send_file(output_path, as_attachment=True)

@app.route("/healthz")
def healthz():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
