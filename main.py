from fastapi import FastAPI
import models
from database import engine
from routers import recordings, merge_sessions
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(recordings.router)
app.include_router(merge_sessions.router)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "LectureMerge backend is running"}