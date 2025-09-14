import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
import os


# --- Extract text from image ---
def extract_text_from_image(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


# --- Extract text from PDF ---
def extract_text_from_pdf(pdf_path):
    text = ""
    pages = convert_from_path(pdf_path, dpi=300)
    for page in pages:
        text += pytesseract.image_to_string(page) + "\n"
    return text


# --- Main processor ---
def process_file_to_text(file_path, join_strategy="smart"):
    """
    Convert uploaded file (PDF, JPG, PNG, TIFF) into plain text.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
        return extract_text_from_image(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF, JPG, PNG, or TIFF.")


# --- Convert text to DOCX ---
def text_to_docx(text):
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
