# processor.py
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path):
    text = ""
    try:
        # Try text extraction first
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        if text.strip():
            return text
    except Exception as e:
        print(f"PDF text extraction failed, falling back to OCR: {e}")

    # Fallback to OCR
    images = convert_from_path(file_path)
    for i, image in enumerate(images):
        ocr_text = pytesseract.image_to_string(image)
        text += ocr_text + "\n"
    return text

def extract_text_from_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)
