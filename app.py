from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
)
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
import stripe

from processor import process_file_to_text, text_to_docx

# -----------------------------
# CONFIG
# -----------------------------
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max upload

# Stripe setup (replace with real keys in Render dashboard env vars)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "price_placeholder")

# -----------------------------
# LOGIN SETUP
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Temporary in-memory user store (replace with database later)
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
        user = USERS.get(username)
        if user and user["password"] == password:
            login_user(User(username, user["plan"]))
            flash("✅ Logged in successfully!")
            return redirect(url_for("index"))
        else:
            flash("❌ Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Logged out.")
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", plan=current_user.plan)

# -----------------------------
# STRIPE CHECKOUT
# -----------------------------
@app.route("/upgrade", methods=["GET"])
@login_required
def upgrade():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("cancel", _external=True),
            customer_email=f"{current_user.id}@example.com",  # placeholder for now
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Error starting checkout: {e}")
        return redirect(url_for("index"))

@app.route("/success")
@login_required
def success():
    # TODO: Update user plan in real DB after webhook confirmation
    current_user.plan = "paid"
    flash("🎉 Subscription successful! You now have Pro access.")
    return render_template("success.html", plan=current_user.plan)

@app.route("/cancel")
@login_required
def cancel():
    flash("❌ Upgrade canceled. You are limited to 5MB file size on the Free plan.")
    return render_template("cancel.html", plan=current_user.plan)

@app.route("/billing-portal")
@login_required
def billing_portal():
    try:
        # Replace with real customer_id from your DB in production
        customer_id = f"cus_{current_user.id}"
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=url_for("index", _external=True),
        )
        return redirect(session.url)
    except Exception as e:
        flash(f"Error opening billing portal: {e}")
        return redirect(url_for("index"))

# -----------------------------
# FILE CONVERSION
# -----------------------------
@app.route("/convert", methods=["POST"])
@login_required
def convert():
    if "file" not in request.files:
        flash("No file selected")
        return redirect(url_for("index"))

    f = request.files["file"]
    if f.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))
    if not allowed_file(f.filename):
        flash("Unsupported file type")
        return redirect(url_for("index"))

    # Enforce plan limits
    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)
    size_mb = file_size / (1024 * 1024)

    if current_user.plan == "free" and size_mb > 5:
        flash("❌ Free plan limit is 5MB. Upgrade to Pro ($16/month) for files up to 50MB.")
        return redirect(url_for("index"))

    if current_user.plan == "paid" and size_mb > 50:
        flash("❌ Pro plan limit is 50MB. Please reduce file size.")
        return redirect(url_for_
