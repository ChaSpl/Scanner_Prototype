# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.edit   import router as edit_router
from app.routes.auth   import router as auth_router

import logging #to silence bcrypt version‐check noise

# silence passlib’s missing‐__about__ warning
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

app = FastAPI()

# 1) Apply CORS (before mounting anything else)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # dev only!
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2) Include your API routers
app.include_router(upload_router)
app.include_router(edit_router)
app.include_router(auth_router)

# 3) Serve timeline images under /static
app.mount(
    "/static", 
    StaticFiles(directory=os.path.join(os.getcwd(), "static")), 
    name="static"
)

# 4) Serve generated PDFs under /pdfs
app.mount(
    "/pdfs",
    StaticFiles(directory=os.path.join(os.getcwd(), "PDFs_Test")),
    name="pdfs"
)

# 5) Serve the React build at the root URL
app.mount(
    "/", 
    StaticFiles(directory="app/frontend/dist", html=True), 
    name="frontend")
