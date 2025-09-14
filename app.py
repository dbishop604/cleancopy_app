import os
import io
import time
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
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

# --- Auto cleanup function ---
def cleanup_old_files(folder, max_age=28800):  # 8 hours = 28800 seconds
    now = time.time()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            age = now - os.path.getmtime(path)
            if age > max_age:
                try:
                    os.remove(path)
                except Exception:
                    pass

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
    return render_template("success.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/coffee")
def coffee():
    return render_template("coffee.html")

@app.route("/convert", methods=["POST"])
def convert():
    # Clean old files before handling new upload
    cleanup_old_files(UPLOAD_FOLDER)
    cleanup_old_files(CONVERTED_FOLDER)

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
    base_name = filename.rsplit(".", 1)[0]
    temp_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")
        fmt = request.form.get("format", "docx")

        if fmt == "txt":
            out_name = base_name + ".txt"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(text)
        else:
            out_name = base_name + ".docx"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            buf = text_to_docx(text)
            with open(out_path, "wb") as out:
                out.write(buf.getbuffer())

        return redirect(url_for("success", file=out_name))

    except Exception as e:
        flash(f"❌ Conversion failed: {e}")
        return redirect(url_for("cancel"))

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(CONVERTED_FOLDER, filename)
    if not os.path.exists(path):
        flash("⚠️ File not found or expired.")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True)

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
