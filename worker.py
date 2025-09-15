import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

# ✅ Add this check at the top of the file
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

# Set up Redis connection
conn = redis.Redis.from_url(redis_url)
q = Queue(connection=conn)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker([q])
        worker.work()
