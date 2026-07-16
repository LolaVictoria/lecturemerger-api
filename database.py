import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# use /tmp for Render since free tier has no persistent disk
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lecture_merge.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()