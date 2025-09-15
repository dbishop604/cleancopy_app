import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

if redis_url.startswith("rediss://"):
    redis_conn = redis.Redis.from_url(redis_url, ssl=True, decode_responses=True)
else:
    redis_conn = redis.Redis.from_url(redis_url, decode_responses=True)

queue = Queue(connection=redis_conn)

if __name__ == "__main__":
    print("🚀 Worker starting up...")
    try:
        redis_conn.ping()
        print("✅ Successfully connected to Redis!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        raise

    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
