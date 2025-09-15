import os
import redis
from rq import Worker, Queue, Connection

# Redis connection (from environment variable REDIS_URL)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = redis.Redis.from_url(redis_url)

# Queues to listen on
listen = ["default"]


def run_worker():
    """Start the RQ worker and listen for jobs on the 'default' queue."""
    with Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        print("🚀 Worker started, listening for jobs on:", listen)
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()
