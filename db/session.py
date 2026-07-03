from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL
from db.models import Base

_kwargs = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Add itinerary_json column if not exists (safe migration for existing DBs)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE applications ADD COLUMN itinerary_json JSON"))
            conn.commit()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
