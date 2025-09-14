import os
import sys
import time
import traceback
from redis import Redis
from rq import Connection, Worker
from processor import process_file

# Redis connection
redis_url = os.environ.get("REDIS_URL")
if not redis_url:
    print("❌ ERROR: REDIS_URL not set.")
    sys.exit(1)

redis_conn = Redis.from_url(redis_url)

# Job function
def process_file_job(input_path, output_path):
    try:
        print(f"🚀 Starting OCR job: {input_path} -> {output_path}")
        process_file(input_path, output_path)
        print(f"✅ Job complete: {output_path}")
        return {"status": "done", "output": output_path}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Error in job: {e}\n{tb}")
        return {"status": "error", "message": str(e)}

# Start worker
if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(["default"])
        print("👷 Worker started, waiting for jobs...")
        worker.work(with_scheduler=True)
