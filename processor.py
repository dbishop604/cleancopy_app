import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
import os
import tempfile

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
        # Convert PDF pages to images
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
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in
