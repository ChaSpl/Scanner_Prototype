# DevHelperCode/init_db.py

import os
import sys

# 1) Make sure we can import your app package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 2) Point exactly at your SQLite file
db_file = r"C:\Users\chasp\Documents\WORK\SKILL SCANNER\SKSC_Prototype\db\database.sqlite"
db_url  = f"sqlite:///{db_file}"

from app.models import Base
from sqlalchemy import create_engine

engine = create_engine(db_url, echo=True)
print("Creating tables in:", db_url)
Base.metadata.create_all(bind=engine)
