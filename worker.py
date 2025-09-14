import os
import sys
import redis
from rq import Connection, Worker
from processor import process_file_job  # Ensure this is implemented properly

# Add current directory to sys.path
sys.path.append(os.path.dirname(__file__))

# Listen to the 'default' queue
listen = ['default']

# Redis connection URL (Render default: localhost, port 6379, DB 0)
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# ⚠️ Use SSL only if you're connecting to a hosted Redis with TLS (like Redis Cloud)
try:
    conn = redis.from_url(redis_url, ssl=False, decode_responses=False)
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    conn = None

if __name__ == '__main__':
    if not conn:
        print("❌ No Redis connection available. Exiting.")
        sys.exit(1)

    print("✅ Redis connection established. Starting worker...")

    with Connection(conn):
        worker = Worker(map(str, listen))
        worker.work()
