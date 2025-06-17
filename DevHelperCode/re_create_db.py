from app.models import Base
from db.session import engine
Base.metadata.create_all(bind=engine)
