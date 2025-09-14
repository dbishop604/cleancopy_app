from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os, tempfile
from processor import process_file_to_text, text_to_docx

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    # Enforce Terms agreement
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
        # Save uploaded file to a temporary path
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.filename)[1])
        f.save(tmp.name)

        # Step 1: Run OCR → plain text
        text = process_file_to_text(tmp.name)

        # Step 2: Convert text → DOCX file (returns BytesIO)
        buf = text_to_docx(text)

        # Step 3: Clean up temp file
        os.unlink(tmp.name)

        # Step 4: Send DOCX to user
        return send_file(
            buf,
            as_attachment=True,
            download_name=os.path.splitext(f.filename)[0] + ".docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print("Conversion error:", e)
        flash("Something went wrong during conversion. Please try again.", "error")
        return redirect(url_for("index"))
