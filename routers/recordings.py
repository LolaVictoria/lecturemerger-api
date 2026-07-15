import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from dependencies import get_db
import models
import schemas
from services.transcription import transcribe_audio

router = APIRouter(prefix="/recordings", tags=["recordings"])

UPLOAD_DIR = "uploads"

def run_transcription(recording_id: int, audio_path: str):
    """
    Background task: transcribes audio and saves chunks to database.
    Runs after the upload response is already sent to the user.
    """
    # get a fresh database session for this background task
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        # update status to transcribing
        recording = db.query(models.Recording).filter(
            models.Recording.id == recording_id
        ).first()
        
        if not recording:
            return
        
        recording.status = "transcribing"
        db.commit()
        
        # run whisper
        chunks = transcribe_audio(audio_path)
        
        # save each chunk to the database
        for chunk in chunks:
            transcript_chunk = models.TranscriptChunk(
                recording_id=recording_id,
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                text=chunk["text"]
            )
            db.add(transcript_chunk)
        
        # update status to transcribed
        recording.status = "transcribed"
        db.commit()
        
    except Exception as e:
        # if something goes wrong, mark as error so the user knows
        recording = db.query(models.Recording).filter(
            models.Recording.id == recording_id
        ).first()
        if recording:
            recording.status = "error"
            db.commit()
        print(f"Transcription error for recording {recording_id}: {e}")
    
    finally:
        db.close()


@router.post("/", response_model=schemas.RecordingOut)
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = None,
    db: Session = Depends(get_db)
):
    # validate file type
    if not file.filename.lower().endswith((".mp3", ".wav", ".webm", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail="Invalid audio file type")

    # save file to uploads folder
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # create recording row
    recording = models.Recording(
        title=title or file.filename,
        audio_filename=file.filename,
        status="recording_only"
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    # kick off transcription in the background
    # this runs AFTER the response is sent, so the user doesn't wait
    background_tasks.add_task(
        run_transcription,
        recording.id,
        file_path
    )

    return recording


@router.get("/", response_model=list[schemas.RecordingOut])
def get_all_recordings(db: Session = Depends(get_db)):
    recordings = db.query(models.Recording).all()
    return recordings


@router.get("/{recording_id}", response_model=schemas.RecordingOut)
def get_recording(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(models.Recording).filter(
        models.Recording.id == recording_id
    ).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording


@router.get("/{recording_id}/chunks", response_model=list[schemas.TranscriptChunkOut])
def get_transcript_chunks(recording_id: int, db: Session = Depends(get_db)):
    chunks = db.query(models.TranscriptChunk).filter(
        models.TranscriptChunk.recording_id == recording_id
    ).order_by(models.TranscriptChunk.start_time).all()
    return chunks