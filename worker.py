import os
import redis
from rq import Queue
from processor import process_file_job

q = None  # Queue will be initialized below

def get_queue():
    global q
    if q is None:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("REDIS_URL environment variable is not set.")
        r = redis.Redis.from_url(redis_url)
        q = Queue(connection=r)
    return q


if __name__ == '__main__':
    from time import sleep
    print("Worker is running... waiting for jobs.")
    queue = get_queue()
    while True:
        sleep(1)
