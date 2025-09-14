import os
import sys
import redis
from rq import Connection, Worker
from processor import process_file

# Ensure the app directory is on sys.path
sys.path.append(os.path.dirname(__file__))

listen = ['default']

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
conn = redis.from_url(redis_url)

# Define a worker that will run process_file jobs
if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(str, listen))
        worker.work()
