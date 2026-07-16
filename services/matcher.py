from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
    return model

def match_chunks_to_sections(chunks: list[dict], sections: list[dict]) -> list[dict]:
    if not chunks or not sections:
        return []

    # filter out sections that are just labels with no body text
    # these cause the matcher to dump too many chunks into them
    meaningful_sections = [
        s for s in sections
        if len((s.get("body_text") or "").strip()) > 50
        or len((s.get("heading") or "").strip()) > 30
    ]

    if not meaningful_sections:
        meaningful_sections = sections

    section_texts = []
    for section in meaningful_sections:
        heading = section.get("heading") or ""
        body = section.get("body_text") or ""
        combined = f"{heading}. {body}".strip()
        section_texts.append(combined)

    chunk_texts = [chunk["text"] for chunk in chunks]

    chunk_embeddings = get_model().encode(chunk_texts, show_progress_bar=False)
    section_embeddings = get_model().encode(section_texts, show_progress_bar=False)

    similarity_matrix = cosine_similarity(chunk_embeddings, section_embeddings)

    matches = []
    for chunk_idx, chunk in enumerate(chunks):
        scores = similarity_matrix[chunk_idx]
        best_section_idx = int(np.argmax(scores))
        best_score = float(scores[best_section_idx])

        matches.append({
            "chunk_id": chunk["id"],
            "section_id": meaningful_sections[best_section_idx]["id"],
            "confidence_score": round(best_score, 4)
        })

    return matches
    """
    Takes transcript chunks and PDF sections, returns a list of matches.
    
    chunks: list of dicts with keys: id, text
    sections: list of dicts with keys: id, heading, body_text
    
    Returns: list of dicts with keys:
        chunk_id, section_id, confidence_score
    """

    if not chunks or not sections:
        return []

    # combine heading + body_text for each section so the embedding
    # captures both the title and the content of the section
    section_texts = []
    for section in sections:
        heading = section.get("heading") or ""
        body = section.get("body_text") or ""
        combined = f"{heading}. {body}".strip()
        section_texts.append(combined)

    # get just the text from each chunk
    chunk_texts = [chunk["text"] for chunk in chunks]

    # generate embeddings for both lists
    # encode() converts text into a numerical vector capturing its meaning
    chunk_embeddings = get_model().encode(chunk_texts, show_progress_bar=False)
    section_embeddings = get_model().encode(section_texts, show_progress_bar=False)

    # compute cosine similarity between every chunk and every section
    # result is a matrix: rows = chunks, columns = sections
    # each value is a score between 0 (unrelated) and 1 (identical meaning)
    similarity_matrix = cosine_similarity(chunk_embeddings, section_embeddings)

    # for each chunk, find the section with the highest similarity score
    matches = []
    for chunk_idx, chunk in enumerate(chunks):
        scores = similarity_matrix[chunk_idx]
        best_section_idx = int(np.argmax(scores))
        best_score = float(scores[best_section_idx])

        matches.append({
            "chunk_id": chunk["id"],
            "section_id": sections[best_section_idx]["id"],
            "confidence_score": round(best_score, 4)
        })

    return matches