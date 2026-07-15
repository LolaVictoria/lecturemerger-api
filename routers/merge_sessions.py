import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
import models
import schemas
from services.pdf_parser import extract_sections
from services.matcher import match_chunks_to_sections
import models


router = APIRouter(prefix="/merge-sessions", tags=["merge sessions"])

UPLOAD_DIR = "uploads"

@router.post("/", response_model=schemas.MergeSessionOut)
async def create_merge_session(
    recording_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    recording = db.query(models.Recording).filter(
        models.Recording.id == recording_id
    ).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # save file FIRST
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # create merge session row
    merge_session = models.MergeSession(
        recording_id=recording_id,
        pdf_filename=file.filename,
        status="in_progress"
    )
    db.add(merge_session)
    db.commit()
    db.refresh(merge_session)

    # parse AFTER file is saved
    sections = extract_sections(file_path)

    if not sections:
        raise HTTPException(status_code=400, detail="Could not extract sections from PDF")

    for section in sections:
        pdf_section = models.PdfSection(
            merge_session_id=merge_session.id,
            order_index=section["order_index"],
            heading=section["heading"],
            body_text=section["body_text"],
            page_number=section["page_number"]
        )
        db.add(pdf_section)

    db.commit()
    return merge_session

@router.get("/{session_id}/sections", response_model=list[schemas.PdfSectionOut])
def get_sections(session_id: int, db: Session = Depends(get_db)):
    sections = db.query(models.PdfSection).filter(
        models.PdfSection.merge_session_id == session_id
    ).order_by(models.PdfSection.order_index).all()
    return sections

def is_meaningful_chunk(text: str) -> bool:
    text = text.strip()
    word_count = len(text.split())

    if word_count < 5:
        return False

    filler = {
        "okay", "right", "yeah", "hmm", "um", "uh", "so",
        "alright", "ok", "okay" "yes", "no", "well", "now"
    }
    if word_count <= 3 and text.lower().rstrip(".,!?") in filler:
        return False

    return True

# for matching 
@router.post("/{session_id}/match")
def run_matching(session_id: int, db: Session = Depends(get_db)):
    """
    Runs semantic matching for a merge session.
    Matches transcript chunks to PDF sections and saves results.
    """

    # get the merge session
    session = db.query(models.MergeSession).filter(
        models.MergeSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Merge session not found")

    # get the recording's transcript chunks
    chunks = db.query(models.TranscriptChunk).filter(
        models.TranscriptChunk.recording_id == session.recording_id
    ).all()

    # get the PDF sections for this session
    sections = db.query(models.PdfSection).filter(
        models.PdfSection.merge_session_id == session_id
    ).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found for this recording")
    if not sections:
        raise HTTPException(status_code=400, detail="No PDF sections found for this merge session")

    # convert SQLAlchemy objects to plain dicts for the matcher
    chunk_dicts = [
        {"id": c.id, "text": c.text}
        for c in chunks
        if is_meaningful_chunk(c.text)
    ]
    section_dicts = [
        {"id": s.id, "heading": s.heading, "body_text": s.body_text}
        for s in sections
    ]

    # run the matching
    matches = match_chunks_to_sections(chunk_dicts, section_dicts)

    # save matches back to transcript_chunks table
    # update matched_section_id and match_confidence on each chunk
    for match in matches:
        chunk = db.query(models.TranscriptChunk).filter(
            models.TranscriptChunk.id == match["chunk_id"]
        ).first()
        if chunk:
            chunk.matched_section_id = match["section_id"]
            chunk.match_confidence = match["confidence_score"]

    # also create attached_items rows for each match
    # this populates the editable content layer the student will review
    for match in matches:
        chunk = db.query(models.TranscriptChunk).filter(
            models.TranscriptChunk.id == match["chunk_id"]
        ).first()

        # check if an attached_item already exists for this chunk
        # to avoid duplicates if matching is run more than once
        existing = db.query(models.AttachedItem).filter(
            models.AttachedItem.transcript_chunk_id == match["chunk_id"]
        ).first()

        if not existing and chunk and match["confidence_score"] > 0.35:
            attached_item = models.AttachedItem(
                section_id=match["section_id"],
                item_type="speech",
                order_index=0,
                content_text=chunk.text,
                transcript_chunk_id=chunk.id
            )
            db.add(attached_item)

    db.commit()

    return {
        "message": f"Matched {len(matches)} chunks to sections successfully",
        "matches": matches
    }