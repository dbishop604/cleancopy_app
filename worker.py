import os
from redis import Redis
from rq import Worker, Queue, Connection
from processor import process_file_to_text, text_to_docx

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_file_job(input_path, output_path, job_id):
    """Background job to OCR a file and save DOCX/TXT output with progress tracking."""
    from rq import get_current_job
    job = get_current_job()
    try:
        job.meta["progress"] = 10
        job.save_meta()

        # Extract text
        text = process_file_to_text(input_path, join_strategy="smart")
        job.meta["progress"] = 60
        job.save_meta()

        # Convert to output format
        buf = None
        if output_path.endswith(".txt"):
            with open(output_path, "w", encoding="utf-8") as out_f:
                out_f.write(text)
        else:
            buf = text_to_docx(text)
            with open(output_path, "wb") as out_f:
                out_f.write(buf.getbuffer())

        job.meta["progress"] = 100
        job.save_meta()
        return {"status": "done", "output": output_path}

    except Exception as e:
        job.meta["progress"] = -1
        job.save_meta()
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    redis_url = os.environ.get("REDIS_URL")
    redis_conn = Redis.from_url(redis_url)
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()
