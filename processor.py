import io
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document

# --- Extract text from image ---
def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[Error extracting text from image: {e}]"

# --- Extract text from PDF ---
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # Convert PDF pages to images, then OCR each page
        pages = convert_from_path(pdf_path, dpi=300)
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
    except Exception as e:
        text = f"[Error extracting text from PDF: {e}]"
    return text

# --- Main processor ---
def process_file_to_text(file_path, join_strategy="smart"):
    """
    Convert uploaded file (PDF, JPG, PNG, TIFF) into plain text.
    join_strategy: currently unused placeholder, but can be "smart".
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
        text = extract_text_from_image(file_path)
    elif ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = "[Unsupported file format]"

    # Basic cleanup: strip excessive whitespace if join_strategy == "smart"
    if join_strategy == "smart":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = " ".join(lines)
    return text

# --- Convert text to DOCX ---
def text_to_docx(text):
    """
    Convert plain text into a DOCX file in memory and return BytesIO buffer.
    """
    doc = Document()
    for line in text.splitlines():
        if line.strip():
            doc.add_paragraph(line.strip())
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
