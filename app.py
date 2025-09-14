import os
import io
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_from_directory
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
        return jsonify({"success": False, "message": "You must agree to the terms of service and privacy policy before uploading."}), 400

    if "fileUpload" not in request.files:
        return jsonify({"success": False, "message": "No file selected."}), 400

    f = request.files["fileUpload"]
    if f.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")
        fmt = request.form.get("format", "docx").lower()
        base_name = os.path.splitext(filename)[0]

        if fmt == "txt":
            output_filename = f"{base_name}.txt"
            output_path = os.path.join(CONVERTED_FOLDER, output_filename)
            with open(output_path, "w", encoding="utf-8") as out_f:
                out_f.write(text)
        else:
            output_filename = f"{base_name}.docx"
            output_path = os.path.join(CONVERTED_FOLDER, output_filename)
            buf = text_to_docx(text)
            with open(output_path, "wb") as out_f:
                out_f.write(buf.getvalue())

        return jsonify({
            "success": True,
            "download_url": url_for("download_file", filename=output_filename, _external=True)
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/download/<path:filename>")
def download_file(filename):
    try:
        return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return f"Error serving file: {e}", 500

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
