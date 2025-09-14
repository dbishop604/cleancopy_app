import os
import io
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, send_from_directory
)
from werkzeug.utils import secure_filename
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

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

@app.route("/success")
def success():
    download_url = request.args.get("download_url")
    return render_template("success.html", download_url=download_url)

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/coffee")
def coffee():
    return render_template("coffee.html")

@app.route("/download/<filename>")
def download_file(filename):
    """
    Serve converted file for download.
    """
    return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=True)

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
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        # Extract text
        text = process_file_to_text(temp_path, join_strategy="smart")

        # Choose format
        fmt = request.form.get("format", "docx")
        base_name = filename.rsplit(".", 1)[0]
        if fmt == "txt":
            new_filename = base_name + ".txt"
            out_path = os.path.join(CONVERTED_FOLDER, new_filename)
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(text)
        else:
            new_filename = base_name + ".docx"
            buf = text_to_docx(text)
            out_path = os.path.join(CONVERTED_FOLDER, new_filename)
            with open(out_path, "wb") as out:
                out.write(buf.getbuffer())

        # Redirect to success page with download link
        return redirect(url_for("success", download_url=url_for("download_file", filename=new_filename)))

    except Exception as e:
        flash(f"❌ Conversion failed: {e}")
        return redirect(url_for("cancel"))

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
