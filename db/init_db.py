from sqlalchemy import create_engine
from app.models import Base

# Create a database engine — this points to your local file
engine = create_engine("sqlite:///database.sqlite")

def init_db():
    # Create all tables defined in models.py
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
