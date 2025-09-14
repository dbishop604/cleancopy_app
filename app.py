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

# Use shared disk mounted at /app/data
BASE_FOLDER = "/app/data"
UPLOAD_FOLDER = os.path.join(BASE_FOLDER, "uploads")
CONVERTED_FOLDER = os.path.join(BASE_FOLDER, "converted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# --- Redis connection (optional for web) ---
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
    return render_template("coff_
