import os
import sys
import redis
from rq import Connection, Worker
from processor import process_file_job

# Ensure current directory is on sys.path
sys.path.append(os.path.dirname(__file__))

listen = ['default']
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    conn = redis.from_url(redis_url)
    conn.ping()
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    conn = None

if __name__ == "__main__":
    if not conn:
        print("❌ Worker exiting due to Redis error.")
        sys.exit(1)

    with Connection(conn):
        worker = Worker(map(str, listen))
        worker.work()
