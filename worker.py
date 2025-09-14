import os
from redis import Redis
from rq import Worker, Queue, Connection
from processor import process_file_to_text, text_to_docx

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def process_file_job(input_path, output_path, job_id):
    """Background job to OCR a PDF/image and save DOCX output."""
    try:
        text = process_file_to_text(input_path, join_strategy="smart")
        text_to_docx(text, output_path)
        return {"status": "done", "output": output_path}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    redis_conn = Redis.from_url(os.environ["REDIS_URL"])
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()
