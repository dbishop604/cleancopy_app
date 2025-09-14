import os
import io
import logging
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
)
from werkzeug.utils import secure_filename
from processor import process_file_to_text, text_to_docx

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# --- Core Routes ---

@app.route("/")
def index():
    logger.info("Index page loaded")
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
def cancel():
    return render_template("cancel.html")

@app.route("/convert", methods=["POST"])
def convert():
    logger.info("Received file conversion request")

    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of use and privacy policy before uploading.")
        logger.warning("Terms not accepted")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected")
        logger.warning("No file uploaded")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        logger.warning("Empty filename")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)
    logger.info(f"File saved temporarily at {temp_path}")

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")
        logger.info("Text extraction successful")

        fmt = request.form.get("format", "docx")
