# reset_db.py

from app.models import Base
from db.session import engine  # make sure this is your SQLAlchemy engine

# Drop all tables
print("🧨 Dropping all tables...")
Base.metadata.drop_all(bind=engine)

# Create all tables
print("🚧 Creating all tables...")
Base.metadata.create_all(bind=engine)

print("✅ Database reset complete.")
