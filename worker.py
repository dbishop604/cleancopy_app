import os
from redis import Redis
from rq import Connection, Worker

# Redis connection
redis_url = os.environ.get("REDIS_URL")
redis_conn = Redis.from_url(redis_url) if redis_url else None

if __name__ == "__main__":
    if redis_conn:
        with Connection(redis_conn):
            worker = Worker(["default"])  # listens to the "default" queue
            worker.work()
    else:
        print("❌ Redis connection not available. Make sure REDIS_URL is set.")
