import os
import uuid
import redis
import threading
import subprocess
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from worker import enqueue_file

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Redis setup
redis_url = os.getenv('REDIS_URL')
redis_conn = redis.from_url(redis_url)

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/cancel')
def cancel():
    return render_template('cancel.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id + '_' + filename)
        file.save(upload_path)
        
        # Enqueue file for background processing
        enqueue_file(redis_conn, upload_path, file_id)

        return redirect(url_for('success'))
    return redirect(url_for('cancel'))

@app.route('/converted/<file_id>', methods=['GET'])
def get_converted_file(file_id):
    try:
        filepath = os.path.join(app.config['CONVERTED_FOLDER'], f"{file_id}.docx")
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else
