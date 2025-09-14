import os
import io
from flask import (
    Flask, render_template, request, jsonify, send_file
)
from werkzeug.utils import secure_filename
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    if "terms" not in request.form:
        return jsonify({"status": "error", "message": "You must agree to the terms of service and privacy policy."})

    if "fileUpload" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."})

    f = request.files["fileUpload"]
    if f.filename == "":
        return jsonify({"status": "error", "message": "No file selected."})

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")
        fmt = request.form.get("format", "docx")

        if fmt == "txt":
            buf = io.BytesIO(text.encode("utf-8"))
            buf.seek(0)
            return send_file(
                buf,
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".txt",
                mimetype="text/plain"
            )
        else:
            buf = text_to_docx(text)
            buf.seek(0)
            return send_file(
                buf,
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    except Exception as e:
        return jsonify({"status": "error", "message": f"OCR processing failed: {str(e)}"})


# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
