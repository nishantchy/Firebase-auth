from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.services.products_service import get_products
from app.schemas.products import ProductRead
from rq import Queue
from redis import Redis
from app.core.config import settings
from app.redis_queue.jobs import scrape_products_dynamic
from pydantic import BaseModel

router = APIRouter(
    prefix="/api",
    tags=["products"],
)

@router.get("/products", response_model=list[ProductRead])
def read_products(session: Session = Depends(get_session)):
    return get_products(session)

class ScrapeRequest(BaseModel):
    url: str

@router.post("/scrape-products")
def trigger_scrape(request: ScrapeRequest):
    redis_conn = Redis.from_url(settings.REDIS_URL)
    q = Queue(connection=redis_conn)
    job = q.enqueue(scrape_products_dynamic, request.url)
    return {"job_id": job.id, "status": "enqueued"}
