import os
import io
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, jsonify
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
        return jsonify({"status": "error", "message": "You must agree to the terms of service and privacy policy."}), 400

    if "fileUpload" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400

    f = request.files["fileUpload"]
    if f.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")

        fmt = request.form.get("format", "docx")
        base_name = os.path.splitext(filename)[0]

        if fmt == "txt":
            output_path = os.path.join(CONVERTED_FOLDER, base_name + ".txt")
            with open(output_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)
            download_url = url_for("download_file", filename=base_name + ".txt")
        else:
            buf = text_to_docx(text)
            output_path = os.path.join(CONVERTED_FOLDER, base_name + ".docx")
            with open(output_path, "wb") as out_file:
                out_file.write(buf.getvalue())
            download_url = url_for("download_file", filename=base_name + ".docx")

        return jsonify({"status": "success", "download_url": download_url})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(CONVERTED_FOLDER, filename)
    if not os.path.exists(path):
        return "File not found or expired.", 404
    return send_file(path, as_attachment=True)


# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
