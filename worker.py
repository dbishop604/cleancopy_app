import os
from redis import Redis
from rq import Worker, Queue, Connection
from processor import process_file_to_text, text_to_docx

# Shared disk paths (must match app.py and render.yaml)
BASE_FOLDER = "/app/data"
UPLOAD_FOLDER = os.path.join(BASE_FOLDER, "uploads")
CONVERTED_FOLDER = os.path.join(BASE_FOLDER, "converted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def process_file_job(input_path, fmt, output_filename):
    """Background job to OCR a file and save output (DOCX or TXT) into shared folder."""
    try:
        text = process_file_to_text(input_path, join_strategy="smart")

        output_path = os.path.join(CONVERTED_FOLDER, output_filename)

        if fmt == "txt":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            buf = text_to_docx(text)
            with open(output_path, "wb") as f:
                f.write(buf.getvalue())

        return {"status": "done", "output": output_path}

    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable not set for worker service")
    redis_conn = Redis.from_url(redis_url)
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()
