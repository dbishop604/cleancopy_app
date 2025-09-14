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
@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

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

# Temporary in-memory user store (replace with DB later)
USERS = {
    "paiduser": {"password": "paid123", "plan": "paid"},  # sample paid account
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
    flash("👋 Logged out. You are now back on the Free plan (5MB limit).")
    return redirect(url_for("index"))

@app.route("/", methods=["GET"])
def index():
    # If logged in, show Pro plan UI; if not, show Free plan UI
    plan = "free"
    if current_user.is_authenticated:
        plan = getattr(current_user, "plan", "paid")
    return render_template("index.html", plan=plan, user=current_user if current_user.is_authenticated else None)

# -----------------------------
# STRIPE CHECKOUT
# -----------------------------
@app.route("/upgrade", methods=["GET"])
def upgrade():
    if not current_user.is_authenticated:
        # Require login before upgrading
        flash("Please log in or create an account to upgrade.")
        return redirect(url_for("login"))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("cancel", _external=True),
            customer_email=f"{current_user.id}@example.com",  # placeholder
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Error starting checkout: {e}")
        return redirect(url_for("index"))

@app.route("/success")
@login_required
def success():
    if current_user.id in USERS:
        USERS[current_user.id]["plan"] = "paid"
        current_user.plan = "paid"
    flash("🎉 Subscription successful! You now have Pro access (50MB upload limit).")
    return render_template("success.html", plan=current_user.plan)

@app.route("/cancel")
@login_required
def cancel():
    if current_user.id in USERS:
        USERS[current_user.id]["plan"] = "free"
        current_user.plan = "free"
    flash("⚠️ Subscription canceled. You have been moved back to the Free plan (5MB upload limit).")
    return render_template("cancel.html", plan=current_user.plan)

@app.route("/billing-portal")
@login_required
def billing_portal():
    try:
        # Replace with real customer_id from DB in production
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
# TERMS & PRIVACY
# -----------------------------
@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# -----------------------------
# FILE CONVERSION
# -----------------------------
@app.route("/convert", methods=["POST"])
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

    # Determine plan
    if current_user.is_authenticated and getattr(current_user, "plan", "free") == "paid":
        plan = "paid"
        limit_mb = 50
    else:
        plan = "free"
        limit_mb = 5

    # Enforce size limits
    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)
    size_mb = file_size / (1024 * 1024)

    if size_mb > limit_mb:
        flash(f"❌ {plan.capitalize()} plan limit is {limit_mb}MB. Please upgrade or reduce file size.")
        return redirect(url_for("index"))

    # Save file temporarily
    os.makedirs("uploads", exist_ok=True)
    filename = secure_filename(f.filename)
    tmp_path = os.path.join("uploads", filename)
    f.save(tmp_path)

    try:
        # Process file into continuous text while keeping paragraphs
        text = process_file_to_text(tmp_path, join_strategy="paragraphs")

        output_fmt = request.form.get("format", "docx")
        if output_fmt == "txt":
            buf = io.BytesIO(text.encode("utf-8"))
            return send_file(
                buf,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}_cleancopy.txt",
                mimetype="text/plain"
            )
        else:
            docx_buf = text_to_docx(text)
            return send_file(
                docx_buf,
                as_attachment=True,
                download_name=f"{os.path.splitext(filename)[0]}_cleancopy.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    except Exception as e:
        app.logger.exception("Conversion failed")
        flash(f"Conversion failed: {e}")
        return redirect(url_for("index"))
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

