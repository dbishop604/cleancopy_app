from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import io
from processor import process_file_to_text, text_to_docx

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))
    f = request.files["file"]
    if f.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))
    if not allowed_file(f.filename):
        flash("Unsupported file type.")
        return redirect(url_for("index"))

    output_fmt = request.form.get("format", "docx")
    join_strategy = request.form.get("join_strategy", "smart")  # smart | aggressive | none

    filename = secure_filename(f.filename)
    tmp_path = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    f.save(tmp_path)

    try:
        text = process_file_to_text(tmp_path, join_strategy=join_strategy)
        if output_fmt == "txt":
            buf = io.BytesIO(text.encode("utf-8"))
            return send_file(buf, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}_cleancopy.txt", mimetype="text/plain")
        else:
            docx_buf = text_to_docx(text)
            return send_file(docx_buf, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}_cleancopy.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        app.logger.exception("Conversion failed")
        flash(f"Conversion failed: {e}")
        return redirect(url_for("index"))
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
