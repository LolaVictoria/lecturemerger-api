import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import recordings, merge_sessions

# create uploads folder if it doesn't exist
os.makedirs("uploads", exist_ok=True)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://lecturmerge-ui.vercel.app",  
        "*"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recordings.router)
app.include_router(merge_sessions.router)

@app.get("/")
def read_root():
    return {"message": "LectureMerge backend is running"}