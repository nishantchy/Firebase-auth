import os
from sqlmodel import Session, create_engine, SQLModel
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()

def get_session():
    with Session(engine) as session:
        yield session