import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job  # import your processing function

# Get Redis URL from environment variables
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    raise ValueError("❌ REDIS_URL environment variable is not set. Please configure it in Render.")

# Create a Redis connection
conn = redis.Redis.from_url(redis_url)

# Create the default queue
listen = ["default"]

if __name__ == "__main__":
    # Run worker with connection
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
