import os
import io
import time
import threading
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, jsonify, send_file
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

EXPIRY_HOURS = 8


# --- Background cleanup thread ---
def cleanup_files():
    while True:
        try:
            cutoff = time.time() - (EXPIRY_HOURS * 3600)
            for folder in [UPLOAD_FOLDER, CONVERTED_FOLDER]:
                for fname in os.listdir(folder):
                    fpath = os.path.join(folder, fname)
                    if os.path.isfile(fpath):
                        if os.path.getmtime(fpath) < cutoff:
                            os.remove(fpath)
                            print(f"[Cleanup] Removed expired file: {fpath}")
        except Exception as e:
            print(f"[Cleanup Error] {e}")
        time.sleep(600)  # check every 10 minutes


threading.Thread(target=cleanup_files, daemon=True).start()

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

@app.route("/coffee")
def coffee():
    return render_template("coffee.html")

@app.route("/convert", methods=["POST"])
def convert():
    """Handle file upload + conversion and return JSON with download link or error."""
    try:
        # --- Terms check ---
        if "terms" not in request.form:
            return jsonify({"status": "error", "message": "You must agree to the terms before uploading."}), 400

        # --- File check ---
        if "fileUpload" not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded."}), 400

        f = request.files["fileUpload"]
        if f.filename == "":
            return jsonify({"status": "error", "message": "No file selected."}), 400

        filename = secure_filename(f.filename)
        temp_path = os.path.join("/tmp", filename)
        f.save(temp_path)

        # --- Process file ---
        try:
            text = process_file_to_text(temp_path, join_strategy="smart")
        except Exception as e:
            return jsonify({"status": "error", "message": f"OCR failed: {str(e)}"}), 500

        fmt = request.form.get("format", "docx")
        base_name = filename.rsplit(".", 1)[0]

        # Save converted file temporarily
        if fmt == "txt":
            out_name = f"{base_name}.txt"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            with open(out_path, "w", encoding="utf-8") as txtfile:
                txtfile.write(text)
        else:
            out_name = f"{base_name}.docx"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            buf = text_to_docx(text)
            with open(out_path, "wb") as docxfile:
                docxfile.write(buf.getbuffer())

        return jsonify({
            "status": "done",
            "message": "File converted successfully!",
            "download_url": f"/download/{out_name}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500


@app.route("/download/<filename>")
def download(filename):
    """Serve converted file for download."""
    path = os.path.join(CONVERTED_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"status": "error", "message": "File not found (it may have expired)."}), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=filename
    )


# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
