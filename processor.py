import os
from typing import List
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from docx import Document
from docx.shared import Pt
import io

# --- OCR helpers ---

def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """Convert PDF pages to PIL Images."""
    images = convert_from_path(pdf_path, dpi=dpi)
    return images

def image_to_text(img: Image.Image) -> str:
    """OCR a PIL Image to text using Tesseract."""
    config = "--oem 1 --psm 6"
    return pytesseract.image_to_string(img, config=config)

# --- Reflow / cleanup ---

import re
_SENTENCE_END = re.compile(r'[\.!?…””」』」\)]$')
_HYPHEN_LINE_END = re.compile(r'[A-Za-z]-$')

def smart_join_lines(text: str) -> str:
    lines = text.splitlines()
    out_paragraphs = []
    buf = []

    def flush_buf():
        if buf:
            out_paragraphs.append(" ".join(buf).strip())
            buf.clear()

    for raw in lines:
        line = raw.strip()
        if line == "":
            flush_buf()
            continue
        if not buf:
            buf.append(line)
            continue
        prev = buf[-1]

        if _HYPHEN_LINE_END.search(prev) and line and line[0].islower():
            buf[-1] = prev[:]()
