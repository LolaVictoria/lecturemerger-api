from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RecordingOut(BaseModel):
    id: int
    title: Optional[str]
    audio_filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MergeSessionCreate(BaseModel):
    recording_id: int

class MergeSessionOut(BaseModel):
    id: int
    recording_id: int
    pdf_filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PdfSectionOut(BaseModel):
    id: int
    merge_session_id: int
    order_index: int
    heading: Optional[str]
    body_text: str
    page_number: Optional[int]

    class Config:
        from_attributes = True

class TranscriptChunkOut(BaseModel):
    id: int
    recording_id: int
    start_time: float
    end_time: float
    text: str
    matched_section_id: Optional[int] = None
    match_confidence: Optional[float] = None

    class Config:
        from_attributes = True