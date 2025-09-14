import os
import io
import logging
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
)
from werkzeug.utils import secure_filename
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

# Configure logging (so we see errors in Render logs)
logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


# --- Core Routes ---

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
def cancel():
    return render_template("cancel.html")


# --- File Conversion Route ---

@app.route("/convert", methods=["POST"])
def convert():
    try:
        if "terms" not in request.form:
            flash("⚠️ You must agree to the terms of use and privacy policy before uploading.")
            return redirect(url_for("index"))

        if "fileUpload" not in request.files:
            flash("⚠️ No file selected")
            return redirect(url_for("index"))

        f = request.files["fileUpload"]
        if f.filename == "":
            flash("⚠️ No selected file")
            return redirect(url_for("index"))

        filename = secure_filename(f.filename)
        temp_path = os.path.join("/tmp", filename)
        f.save(temp_path)

        app.logger.info(f"File uploaded: {filename}, saved to {temp_path}")

        # Process file with OCR
        text = process_file_to_text(temp_path, join_strategy="smart")

        fmt = request.form.get("format", "docx")
        if fmt == "txt":
