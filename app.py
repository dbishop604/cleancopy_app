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


@app.route("/coffee")
def coffee():
    return render_template("support.html")


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

    filename = secure_filename(f.filen_
