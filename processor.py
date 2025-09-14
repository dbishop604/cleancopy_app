import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
import os

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
        pages = convert_from_path(pdf_path, dpi=300)
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
    except Exception as e:
        text = f"[Error extracting text from PDF: {e}]"
    return text

# --- Main processor ---
def process_file_to_text(file_path, join_strategy="smart"):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".tiff"]:
        return extract_text_from_image(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        return "[Unsupported file type]"

# --- Convert text to DOCX ---
def text_to_docx(text):
    buf = io.BytesIO()
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line.strip())
    doc.save(buf)
    buf.seek(0)
    return buf
