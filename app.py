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

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
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
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of service and privacy policy before uploading.")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected")
        return redirect(url_for("index"))

    if not redis_conn or not q:
        return jsonify({"status": "error", "message": "Redis is not connected. Please try again shortly."}), 500

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")

        fmt = request.form.get("format", "docx")
        if fmt == "txt":
            return send_file(
                io.BytesIO(text.encode("utf-8")),
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".txt",
                mimetype="text/plain"
            )
        else:
            buf = text_to_docx(text)
            return send_file(
                buf,
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Health check for Render ---
@app.route("/healthz")
def healthz():
    return "OK", 200

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
