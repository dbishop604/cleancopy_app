import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
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


@app.route("/convert", methods=["POST"])
def convert():
    # Terms check
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of service and privacy policy before uploading.")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected.")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file.")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        # Convert file to text
        text = process_file_to_text(temp_path, join_strategy="smart")

        # Choose format
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
        flash(f"❌ Conversion failed: {e}")
        return redirect(url_for("cancel"))


# --- Entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
