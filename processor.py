import os
import io
import re
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
    OCR a PIL Image to text using Tesseract.
    """
    config = "--oem 1 --psm 6"  # uniform block of text
    text = pytesseract.image_to_string(img, config=config)
    return text

# --- Reflow / cleanup ---

_SENTENCE_END = re.compile(r'[\.!?…””」』」\)]$')
_HYPHEN_LINE_END = re.compile(r'[A-Za-z]-$')

def smart_join_lines(text: str) -> str:
    """
    Join broken lines into paragraphs while preserving real paragraph breaks.
    """
    lines = text.splitlines()
    out_paragraphs = []
    buf = []

    def flush_buf():
        if buf:
            out_paragraphs.append(" ".join(buf).strip())
            buf.clear()

    for raw in lines:
        line = raw.strip()

        # Paragraph boundary
        if line == "":
            flush_buf()
            continue

        # First line
        if not buf:
            buf.append(line)
            continue

        prev = buf[-1]

        # Hyphenated word
        if _HYPHEN_LINE_END.search(prev) and line and line[0].islower():
            buf[-1] = prev[:-1] + line
            continue

        # No punctuation end, next starts lowercase → join
        if not _SENTENCE_END.search(prev) and line and (line[0].islower() or line[0] in ",;:"):
            buf[-1] = prev + " " + line
            continue

        # New sentence in same paragraph
        if _SENTENCE_END.search(prev):
            buf.append(line)
        else:
            buf[-1] = prev + " " + line

    flush_buf()
    return "\n\n".join(p for p in out_paragraphs if p)

def aggressive_join_lines(text: str) -> str:
    """
    Aggressively strip single line breaks, keep double line breaks.
    """
    text = text.replace("\r\n", "\n")
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
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
        page_texts = [image_to_text(img) for img in pages]
        raw_text = "\n\n".join(page_texts)
    else:
        img = Image.open(path)
        raw_text = image_to_text(img)

    return reflow_text(raw_text, join_strategy=join_strategy)

def text_to_docx(text: str):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    for p in paragraphs:
        doc.add_paragraph(p)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
