import os
import io
import traceback
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
)
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, current_user
from processor import process_file_to_text, text_to_docx

# --- Flask setup ---
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "devkey")

# Upload and converted file storage
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# --- Login / User Management (simple placeholder) ---
login_manager = LoginManager()
login_manager.init_app(app)

class User:
    def __init__(self, id, plan="free"):
        self.id = id
        self.plan = plan

    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, plan="free")  # demo only

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        if email and pw:
            user = User(email, plan="paid")
            login_user(user)
            flash("✅ Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("⚠️ Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    flash("✅ Logged out.", "success")
    return redirect(url_for("index"))

@app.route("/upgrade")
def upgrade():
    flash("✅ Upgrade flow placeholder — integrate Stripe here.", "success")
    return redirect(url_for("index"))

# --- Core Routes ---
@app.route("/")
def index():
    plan = current_user.plan if hasattr(current_user, "plan") else "free"
    return render_template("index.html", plan=plan, user=current_user)

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

# --- File Conversion ---
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
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")

        fmt = request.form.get("format", "docx")
        if fmt == "txt":
            flash("✅ File converted successfully! Your TXT is ready.")
            return send_file(
                io.BytesIO(text.encode("utf-8")),
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".txt",
                mimetype="text/plain"
            )
        else:
            buf = text_to_docx(text)
            flash("✅ File converted successfully! Your DOCX is ready.")
            return send_file(
                buf,
                as_attachment=True,
                download_name=filename.rsplit(".", 1)[0] + ".docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    except Exception as e:
        print("Conversion error:", str(e))
        print(traceback.format_exc())
        flash("❌ Conversion failed. Please try again.")
        return redirect(url_for("cancel"))

# --- Main entrypoint ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
