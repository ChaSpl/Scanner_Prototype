# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.edit import router as edit_router
from app.routes.auth import router as auth_router

app = FastAPI()

# Apply CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                # for dev you can use ["*"], lock down in prod
    allow_credentials=False,            # set to True if you send cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Then mount your routers
app.include_router(upload_router)
app.include_router(edit_router)
app.include_router(auth_router)


