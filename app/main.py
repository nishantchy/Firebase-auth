from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router

create_db_and_tables()

app = FastAPI(
     title="Firebase Authentication",
    description="Backend API for Firebase Authentication",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #development 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)

print(settings.DATABASE_URL)


@app.get("/")
async def root():
    return "Server running at http://localhost:8000"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)