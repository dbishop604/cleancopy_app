import os
import time
import redis
from rq import Worker, Queue, Connection
from processor import process_file

# Redis connection (use REDIS_URL from environment)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = redis.Redis.from_url(redis_url)

# Define queues
listen = ["default"]

def run_worker():
    with Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        worker.work(with_scheduler=True)

if __name__ == "__main__":
    print("🚀 Worker started, listening for jobs...")
    run_worker()
