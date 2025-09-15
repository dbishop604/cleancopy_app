import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

redis_conn = redis.from_url(redis_url, decode_responses=True)
queue = Queue(connection=redis_conn)

# Test Redis connection at startup
try:
    redis_conn.ping()
    print("✅ Worker connected to Redis successfully")
except Exception as e:
    print(f"❌ Worker failed to connect to Redis: {e}")
    raise

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
