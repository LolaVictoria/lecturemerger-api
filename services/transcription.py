import whisper
import os
from typing import List, Dict


model = whisper.load_model("small")

def transcribe_audio(audio_path: str) -> List[Dict]:
    """
    Takes a path to an audio file, transcribes it using Whisper,
    and returns a list of timestamped chunks.
    
    Each chunk looks like:
    {
        "start_time": 0.0,
        "end_time": 4.5,
        "text": "So today we are going to talk about atoms..."
    }
    """
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # transcribe — word_timestamps=True gives us more granular timing
    result = model.transcribe(audio_path, verbose=False)
    
    chunks = []
    
    for segment in result["segments"]:
        chunk = {
            "start_time": round(segment["start"], 2),
            "end_time": round(segment["end"], 2),
            "text": segment["text"].strip()
        }
        # skip empty segments
        if chunk["text"]:
            chunks.append(chunk)
    
    return chunks