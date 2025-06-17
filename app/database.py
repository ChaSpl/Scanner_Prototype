from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Path to your existing SQLite database file
SQLALCHEMY_DATABASE_URL = "sqlite:///db/database.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
