import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

redis_conn = redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

# Log to confirm Redis connection
try:
    redis_conn.ping()
    print("✅ Worker connected to Redis at:", redis_url)
except Exception as e:
    print("❌ Worker failed to connect to Redis:", e)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
