import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

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
    return User
