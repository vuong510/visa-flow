from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL
from db.models import Base

_kwargs = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Safe migrations for existing DBs
    for col_sql in [
        "ALTER TABLE applications ADD COLUMN itinerary_json JSON",
        "ALTER TABLE applications ADD COLUMN extracted_info_json JSON",
        "ALTER TABLE feedbacks ADD COLUMN triage_batch VARCHAR(64)",
        "ALTER TABLE feedbacks ADD COLUMN triage_status VARCHAR(20)",
    ]:
        try:
            with engine.connect() as conn:
                conn.execute(text(col_sql))
                conn.commit()
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
