import os
import uuid
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from redis import Redis
from rq import Queue
from processor import process_file_job

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure upload/output folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Redis connection
try:
    redis_conn = Redis(host='localhost', port=6379)
    redis_conn.ping()
except Exception as e:
    print("Redis connection failed:", e)

# Task queue
q = Queue(connection=redis_conn)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        output_format = request.form.get('format')

        if not uploaded_file or not output_format:
            return 'Missing file or format.', 400

        filename = secure_filename(uploaded_file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        uploaded_file.save(file_path)

        job = q.enqueue(process_file_job, file_path, output_format, file_id)

        return jsonify({"job_id": job.id, "message": "File uploaded and job queued."})

    return render_template('index.html')

@app.route('/status/<job_id>')
def job_status(job_id):
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({"status": "not found"}), 404
    if job.is_finished:
        return jsonify({"status": "finished", "result": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed"})
    else:
        return jsonify({"status": "in progress"})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
