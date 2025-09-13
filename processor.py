import os
from typing import List
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from docx import Document
from docx.shared import Pt

# --- OCR helpers ---

def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images.
    Requires poppler to be installed and on PATH.
    """
    images = convert_from_path(pdf_path, dpi=dpi)
    return images

def image_to_text(img: Image.Image) -> str:
    """
    OCR a PIL Image to text using Tesseract with a page segmentation mode
    that favors blocks into paragraphs.
    """
    # --psm 4 (assume block of text), 6 (assume uniform block of text)
    config = "--oem 1 --psm 6"
    text = pytesseract.image_to_string(img, config=config)
    return text

# --- Reflow / cleanup ---

import re

_SENTENCE_END = re.compile(r'[\.!?…””」』」\)]$')
_HYPHEN_LINE_END = re.compile(r'[A-Za-z]-$')

def smart_join_lines(text: str) -> str:
    """
    Join broken lines into paragraphs while preserving real paragraph breaks.
    Heuristics:
      - If a line ends with hyphen and next line starts with lowercase, remove hyphen and join.
      - If a line does NOT end with sentence punctuation and next line starts lowercase, join with space.
      - Preserve blank lines as paragraph separators.
    """
    lines = text.splitlines()
    out_paragraphs = []
    buf = []

    def flush_buf():
        if buf:
            out_paragraphs.append(" ".join(buf).strip())
            buf.clear()

    for i, raw in enumerate(lines):
        line = raw.strip()

        # Paragraph boundary on empty line
        if line == "":
            flush_buf()
            continue

        # First line in buffer
        if not buf:
            buf.append(line)
            continue

        prev = buf[-1]

        # Hyphenated word split across lines
        if _HYPHEN_LINE_END.search(prev) and (len(line) > 0 and line[0].islower()):
            buf[-1] = prev[:-1] + line  # drop hyphen, join directly
            continue

        # If previous line doesn't look like end of sentence, and next starts lowercase or comma/;/:, join
        if not _SENTENCE_END.search(prev) and (len(line) > 0 and (line[0].islower() or line[0] in ",;:")):
            buf[-1] = prev + " " + line
            continue

        # Otherwise, treat as new sentence in same paragraph
        # If prev ended with end punctuation, start a new sentence but same paragraph
        if _SENTENCE_END.search(prev):
            buf.append(line)
        else:
            # fallback join with space
            buf[-1] = prev + " " + line

    flush_buf()
    # Join paragraphs with a blank line between them
    return "\n\n".join(p for p in out_paragraphs if p)

def aggressive_join_lines(text: str) -> str:
    """
    Aggressively strip all single line breaks, keep double line breaks as paragraphs.
    """
    # Normalize Windows line endings
    text = text.replace("\r\n", "\n")
    # Preserve double newlines, remove single
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize paragraph spacing
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def reflow_text(raw_text: str, join_strategy: str = "smart") -> str:
    raw_text = raw_text.strip()
    if join_strategy == "aggressive":
        return aggressive_join_lines(raw_text)
    elif join_strategy == "none":
        return raw_text
    else:
        return smart_join_lines(raw_text)

# --- Main entrypoints ---

def process_file_to_text(path: str, join_strategy: str = "smart") -> str:
    ext = os.path.splitext(path)[1].lower()
    raw_text = ""
    if ext == ".pdf":
        pages = pdf_to_images(path, dpi=300)
        page_texts = []
        for idx, img in enumerate(pages, start=1):
            page_texts.append(image_to_text(img))
        raw_text = "\n\n".join(page_texts)
    else:
        img = Image.open(path)
        raw_text = image_to_text(img)

    # Reflow into continuous text
    return reflow_text(raw_text, join_strategy=join_strategy)

def text_to_docx(text: str):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Split on blank lines as paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    for p in paragraphs:
        doc.add_paragraph(p)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
