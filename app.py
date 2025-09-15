import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
from worker import get_queue

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")
app.config['UPLOAD_FOLDER'] = '/data/uploads'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part", "status": "error"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file", "status": "error"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Lazy load processor to avoid import-time Redis error
    from processor import process_file_job
    q = get_queue()
    job = q.enqueue(process_file_job, file_path)

    return jsonify({"message": "File received", "job_id": job.id, "status": "success"})

@app.route('/status/<job_id>', methods=['GET'])
def check_status(job_id):
    q = get_queue()
    job = q.fetch_job(job_id)
    if not job:
        return jsonify({"message": "Invalid job ID", "status": "error"}), 404

    if job.is_finished:
        return jsonify({"status": "complete", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)})
    else:
        return jsonify({"status": "processing"})

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
