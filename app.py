from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import os
import io

from processor import process_file_to_text, text_to_docx

# -----------------------------
# Config
# -----------------------------
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit

# -----------------------------
# LOGIN SETUP
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Simple in-memory user store (replace with DB later)
USERS = {
    "freeuser": {"password": "free123", "plan": "free"},
    "paiduser": {"password": "paid123", "plan": "paid"},
}

class User(UserMixin):
    def __init__(self, username, plan):
        self.id = username
        self.plan = plan

@login_manager.user_loader
def load_user(user_id):
    user = USERS.get(user_id)
    if user:
        return User(user_id, user["plan"])
    return None

# -----------------------------
# ROUTES
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please enter both username and password")
            return redirect(url_for("login"))

        user = USERS.get(username)
        if user and user["password"] == password:
            login_user(User(username, user["plan"]))
            flash(f"Welcome back, {username}!")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", plan=current_user.plan)

@app.route("/convert", methods=["POST"])
@login_required
def convert():
    # Enforce limits based on plan
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

    # File size check depending on plan
    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)

    max_size = 10 * 1024 * 1024 if current_user.plan == "free" else 50 * 1024 * 1024
    if file_size > max_size:
        flash(f"{current_user.plan.capitalize()} users can only upload files up to {max_size // (1024*1024)} MB.")
        return redirect(url_for("index"))

    output_fmt = request.form.get("format", "docx")
    join_strategy = request.form.get("join_strategy", "smart")

    filename = secure_filename(f.filename)
    os.makedirs(
