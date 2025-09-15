import os
import redis
from rq import Worker, Queue, Connection

from processor import process_file_job

redis_url = os.getenv("REDIS_URL")
conn = redis.Redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        q = Queue()
        worker = Worker([q])
        worker.work()
