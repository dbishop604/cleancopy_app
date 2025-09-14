import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, current_user

from processor import process_file_to_text, text_to_docx

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

# Limit uploads (50 MB max, plan logic handled separately)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# -----------------------------
# LOGIN / USER MGMT (placeholder)
# -----------------------------

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

# -----------------------------
# CORE ROUTES
# -----------------------------

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

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("⚠️ Please fill out all fields.", "error")
            return redirect(url_for("contact"))

        flash("✅ Your message has been received (placeholder).", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

# -----------------------------
# FILE CONVERSION
# -----------------------------
@app.route("/convert", methods=["POST"])
def convert():
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of use and privacy policy before uploading.", "error")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected", "error")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file", "error")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    temp_path = os.path.join("/tmp", filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")

        if request.form.get("format") == "txt":
            return send_file(
                io.BytesIO(text.encode("utf-8")),
                as_attachment=True,
                dow
