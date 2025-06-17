# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.edit   import router as edit_router
from app.routes.auth   import router as auth_router

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

# 3) Serve the React build at the root URL
app.mount(
    "/", 
    StaticFiles(directory="app/frontend/dist", html=True), 
    name="frontend")
