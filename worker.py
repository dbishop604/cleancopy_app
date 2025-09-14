import os
from redis import Redis
from rq import Worker, Queue, Connection
from processor import process_file_to_text, text_to_docx
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# Shared disk paths
BASE_FOLDER = "/app/data"
UPLOAD_FOLDER = os.path.join(BASE_FOLDER, "uploads")
CONVERTED_FOLDER = os.path.join(BASE_FOLDER, "converted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Redis connection
redis_url = os.environ.get("REDIS_URL")
if not redis_url:
    raise RuntimeError("REDIS_URL environment variable not set for worker service")

redis_conn = Redis.from_url(redis_url)

def process_file_job(file_path, fmt, output_filename):
    """Background job to OCR a file with progress tracking."""
    from rq import get_current_job
    job = get_current_job()

    text_output = []
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            pages = convert_from_path(file_path)
            total = len(pages)
            for i, page in enumerate(pages, start=1):
                page_text = pytesseract.image_to_string(page)
                text_output.append(page_text.strip())
                # Save progress into job.meta
                job.meta["progress"] = int(i / total * 100)
                job.save_meta()
        elif ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            image = Image.open(file_path)
            page_text = pytesseract.image_to_string(image)
            text_output.append(page_text.strip())
            job.meta["progress"] = 100
            job.save_meta()
        else:
            raise ValueError("Unsupported file type")

        text = "\n\n".join([p for p in text_output if p])

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
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()
