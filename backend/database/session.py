from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base

DATABASE_URL = "postgresql://adera_user:adera_dev_password@localhost:5432/adera_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()