import os
import redis
from rq import Worker, Queue, Connection
from processor import process_file_job

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable is not set.")

conn = redis.from_url(redis_url)
queue = Queue(connection=conn)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker([queue])
        worker.work()
