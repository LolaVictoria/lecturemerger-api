from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    audio_filename = Column(String, nullable=False)
    status = Column(String, default="recording_only")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    matched_section_id = Column(Integer, ForeignKey("pdf_sections.id"), nullable=True)
    match_confidence = Column(Float, nullable=True)


class MergeSession(Base):
    __tablename__ = "merge_sessions"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    pdf_filename = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PdfSection(Base):
    __tablename__ = "pdf_sections"

    id = Column(Integer, primary_key=True, index=True)
    merge_session_id = Column(Integer, ForeignKey("merge_sessions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    heading = Column(String, nullable=True)
    body_text = Column(String, nullable=False)
    page_number = Column(Integer, nullable=True)


class AttachedItem(Base):
    __tablename__ = "attached_items"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("pdf_sections.id"), nullable=False)
    item_type = Column(String, nullable=False)  # 'speech' or 'note'
    order_index = Column(Integer, nullable=False)
    content_text = Column(String, nullable=False)
    transcript_chunk_id = Column(Integer, ForeignKey("transcript_chunks.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())