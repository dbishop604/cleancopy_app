import os
import io
from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, jsonify
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
    # Health check + main page
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

# --- File conversion ---
@app.route("/convert", methods=["POST"])
def convert():
    try:
        if "terms" not in request.form:
            return jsonify({"error": "⚠️ You must agree to the terms of service and privacy policy before uploading."}), 400

        if "fileUpload" not in request.files:
            return jsonify({"error": "⚠️ No file uploaded."}), 400

        f = request.files["fileUpload"]
        if f.filename == "":
            return jsonify({"error": "⚠️ No file selected."}), 400

        filename = secure_filename(f.filename)
        temp_path = os.path.join("/tmp", filename)
        f.save(temp_path)

        # Process file
        text = process_file_to_text(temp_path, join_strategy="smart")
        fmt = request.form.get("format", "docx")

        if fmt == "txt":
            buf = io.BytesIO(text.encode("utf-8"))
            return send_file(
                buf,
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
        return jsonify({"error": f"❌ Conversion failed: {str(e)}"}), 500

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
