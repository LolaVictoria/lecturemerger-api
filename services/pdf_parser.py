import fitz
from typing import List, Dict

MIN_BODY_LENGTH = 40

def extract_sections(pdf_path: str) -> List[Dict]:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open PDF: {e}")
        return []

    raw_blocks = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    size = span.get("size", 0)
                    flags = span.get("flags", 0)
                    is_bold = bool(flags & 2**4)
                    raw_blocks.append({
                        "text": text,
                        "size": size,
                        "is_bold": is_bold,
                        "page_number": page_num + 1
                    })

    doc.close()

    if not raw_blocks:
        return []

    sizes = [b["size"] for b in raw_blocks]
    body_size = max(set(sizes), key=sizes.count)

    print(f"body_size detected: {body_size}")
    print(f"total raw_blocks: {len(raw_blocks)}")

    sections = []
    order_index = 0
    current_section = None

    for block in raw_blocks:
        text = block["text"]
        size = block["size"]
        is_bold = block["is_bold"]
        page = block["page_number"]

        is_larger = size > body_size + 1
        is_heading = (is_larger or is_bold) and not _is_bullet_label(text)

        if is_heading:
            if current_section:
                if len(current_section["body_text"].strip()) >= MIN_BODY_LENGTH:
                    sections.append(current_section)
                    order_index += 1
                elif sections:
                    sections[-1]["body_text"] += " " + current_section["body_text"]

            current_section = {
                "heading": text,
                "body_text": "",
                "page_number": page,
                "order_index": order_index
            }
        else:
            if current_section is None:
                current_section = {
                    "heading": None,
                    "body_text": "",
                    "page_number": page,
                    "order_index": order_index
                }
            current_section["body_text"] += " " + text

    if current_section:
        if len(current_section["body_text"].strip()) >= MIN_BODY_LENGTH:
            sections.append(current_section)
        elif sections:
            sections[-1]["body_text"] += " " + current_section["body_text"]

    for i, s in enumerate(sections):
        s["order_index"] = i

    print(f"Sections found: {len(sections)}")
    for s in sections[:5]:
        print(f"  heading='{s['heading']}', body_len={len(s['body_text'].strip())}")

    return sections


def _is_bullet_label(text: str) -> bool:
    cleaned = text.lstrip("•·-– ").strip()

    if cleaned.endswith(":") and " " not in cleaned:
        return True

    word_count = len(cleaned.split())
    if word_count <= 2 and len(cleaned) < 20:
        return True

    if all(c in "•·-–•*: " for c in cleaned):
        return True

    return False