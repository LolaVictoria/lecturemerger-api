# LectureMerge — API

Backend for LectureMerge, a tool that automatically merges a lecturer's spoken explanations into the right sections of a course PDF.

## What it does

Students often lose the verbal elaborations a lecturer adds during class — the examples, clarifications, and context that never make it into the PDF slides. LectureMerge solves this by:

1. Transcribing a lecture recording using OpenAI Whisper
2. Parsing the course PDF into sections
3. Using semantic embeddings (sentence-transformers) to match each spoken chunk to the most relevant PDF section
4. Exposing a review API so students can confirm, reassign, or remove matches before generating a merged document

## Tech Stack

- **Python** + **FastAPI** — REST API
- **OpenAI Whisper** — speech-to-text transcription
- **PyMuPDF (fitz)** — PDF parsing and section extraction
- **sentence-transformers** — semantic embedding and cosine similarity matching
- **SQLite** + **SQLAlchemy** — data persistence

lecture-merge/
├── main.py                  # FastAPI app entry point
├── models.py                # SQLAlchemy database models
├── schemas.py               # Pydantic request/response schemas
├── database.py              # Database connection setup
├── dependencies.py          # Shared FastAPI dependencies
├── routers/
│   ├── recordings.py        # Audio upload and transcription endpoints
│   └── merge_sessions.py    # PDF upload, matching, and review endpoints
└── services/
├── transcription.py     # Whisper transcription service
├── pdf_parser.py        # PDF section extraction
└── matcher.py           # Semantic matching service

## Database Schema

Five tables: `recordings`, `transcript_chunks`, `merge_sessions`, `pdf_sections`, `attached_items` — designed so recordings and merge sessions are decoupled, allowing a recording to be merged with different PDFs at different times.

## Setup

```bash
# Clone the repo
git clone https://github.com/LolaVictoria/lecturmerge-api.git
cd lecturmerge-api

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install fastapi uvicorn python-multipart sqlalchemy \
  openai-whisper pymupdf sentence-transformers scikit-learn

# Install ffmpeg (required by Whisper)
# Windows: winget install ffmpeg --source winget
# Mac: brew install ffmpeg

# Run the server
python -m uvicorn main:app --reload
```

API will be available at `http://127.0.0.1:8000`
Interactive docs at `http://127.0.0.1:8000/docs`

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recordings/` | Upload audio, triggers background transcription |
| GET | `/recordings/{id}` | Check transcription status |
| GET | `/recordings/{id}/chunks` | Get timestamped transcript chunks |
| POST | `/merge-sessions/` | Upload PDF and create merge session |
| POST | `/merge-sessions/{id}/match` | Run semantic matching |
| GET | `/merge-sessions/{id}/sections` | Get parsed PDF sections |

## Notes

- First run downloads Whisper and sentence-transformer models (~300MB total, cached after first use)
- Transcription speed depends on audio length and hardware — CPU transcription takes roughly 3-5x audio duration
- The `base` or `small` Whisper model is recommended for production use; `tiny` is faster but less accurate
- **scikit-learn** — cosine similarity computation

## Project Structure
