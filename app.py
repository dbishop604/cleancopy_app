import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from processor import process_file_to_text, text_to_docx

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

# Limit uploads (5MB free, 50MB pro handled in your plan logic)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# -----------------------------
# LOGIN / USER MGMT (placeholder logic for now)
# -----------------------------

login_manager = LoginManager()
login_manager.init_app(app)

class User:
    def __init__(self, id, plan="free"):
        self.id = id
        self.plan = plan

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    # Demo: everyone loads as free unless session updated
    return User(user_id, plan="free")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        # Dummy auth
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
    # Placeholder upgrade flow
    flash("✅ Upgrade flow placeholder — here you’d integrate Stripe.", "success")
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

# -----------------------------
# CONTACT (placeholder)
# -----------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("⚠️ Please fill out all fields.", "error")
            return redirect(url_for("contact"))

        # Placeholder for now
        flash("✅ Your message has been received (this is a placeholder).", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

# -----------------------------
# FILE CONVERSION
# -----------------------------
@app.route("/convert", methods=["POST"])
def convert():
    # Check Terms agreement
    if "terms" not in request.form:
        flash("⚠️ You must agree to the Terms of Use and Privacy Policy before uploading.", "error")
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
                download_name="output.txt",
                mimetype="text/plain",
            )
        else:
            buf = text_to_docx(text)
            return send_file(
                buf,
                as_attachment=True,
                download_name="output.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    except Exception as e:
        flash(f"❌ Error processing file: {e}", "error")
        return redirect(url_for("index"))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
