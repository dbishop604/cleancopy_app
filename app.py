import os
import io
import threading
import uuid
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, jsonify
)
from werkzeug.utils import secure_filename
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

UPLOAD_FOLDER = "/app/uploads"   # use persistent disk
CONVERTED_FOLDER = "/app/uploads/converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# In-memory task status and results
tasks = {}

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

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
    f.save(upload_path)

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "result": None, "filename": filename}

    def run_task():
        try:
            text = process_file_to_text(upload_path, join_strategy="smart")
            fmt = request.form.get("format", "docx")
            base = os.path.splitext(filename)[0]
            if fmt == "txt":
                output_path = os.path.join(CONVERTED_FOLDER, f"{base}_{task_id}.txt")
                with open(output_path, "w", encoding="utf-8") as out:
                    out.write(text)
                tasks[task_id] = {"status": "done", "path": output_path, "download": f"{base}.txt"}
            else:
                buf = text_to_docx(text)
                output_path = os.path.join(CONVERTED_FOLDER, f"{base}_{task_id}.docx")
                with open(output_path, "wb") as out:
                    out.write(buf.getbuffer())
                tasks[task_id] = {"status": "done", "path": output_path, "download": f"{base}.docx"}
        except Exception as e:
            tasks[task_id] = {"status": "error", "message": str(e)}

    threading.Thread(target=run_task, daemon=True).start()
    return redirect(url_for("processing", task_id=task_id))

@app.route("/processing/<task_id>")
def processing(task_id):
    return render_template("processing.html", task_id=task_id)

@app.route("/status/<task_id>")
def status(task_id):
    info = tasks.get(task_id)
    if not info:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify(info)

@app.route("/download/<task_id>")
def download(task_id):
    info = tasks.get(task_id)
    if not info or info.get("status") != "done":
        return "Not ready", 404
    return send_file(
        info["path"],
        as_attachment=True,
        download_name=info["download"]
    )

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
