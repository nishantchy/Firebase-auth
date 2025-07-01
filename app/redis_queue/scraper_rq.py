from rq import Queue
from redis import Redis
from app.core.config import settings
from app.redis_queue.jobs import scrape_daraz_products

# Connect to Redis
redis_conn = Redis.from_url(settings.REDIS_URL)

# Create a queue
q = Queue(connection=redis_conn)

# Enqueue the job
job = q.enqueue(scrape_daraz_products)
print(f"Job {job.id} added to queue at {job.enqueued_at}")