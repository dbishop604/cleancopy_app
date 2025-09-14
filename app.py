from flask import Flask, render_template, request, redirect, url_for, flash
import os

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

    # Example success flow
    # Here you’d call processor.py functions to handle the file
    # text = process_file_to_text(f)
    # output = text_to_docx(text)
    # return send_file(output, as_attachment=True)

    flash("File uploaded and is being processed!", "success")
    return redirect(url_for("index"))
