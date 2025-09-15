import os
import redis
from rq import Worker, Queue, Connection
from processor import extract_text_from_pdf, extract_text_from_image

# Get Redis connection
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")
redis_conn = redis.from_url(redis_url)

# Define the job processing function
def process_file_job(file_path):
    try:
        output_folder = "/data/output"
        os.makedirs(output_folder, exist_ok=True)

        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        output_file = os.path.join(output_folder, f"{name}.txt")
        ext = ext.lower()

        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            text = extract_text_from_image(file_path)
        else:
            return f"Unsupported file type: {ext}"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text.strip() or "[No readable text found]")

        return os.path.basename(output_file)

    except Except
