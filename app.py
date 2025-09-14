from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
from processor import process_file_to_text, text_to_docx

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    # Check Terms agreement
    if "terms" not in request.form:
        flash("You must agree to the Terms of Use and Privacy Policy before uploading.", "error")
        return redirect(url_for("index"))

    # File upload checks
    if "fileUpload" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("No selected file.", "error")
        return redirect(url_for("index"))

    try:
        # Step 1: Run OCR → plain text
        text = process_file_to_text(f)

        # Step 2: Convert text → DOCX file
        output_path = text_to_docx(text)

        # Step 3: Send back file as download
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("Conversion error:", e)
        flash("Something went wrong during conversion. Please try again.", "error")
        return redirect(url_for("index"))
