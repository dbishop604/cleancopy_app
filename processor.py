import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        text = text.strip()

        if not text:
            images = convert_from_path(pdf_path)
            for image in images:
                text += pytesseract.image_to_string(image)
    except Exception as e:
        text = f"[Error processing PDF: {e}]"
    return text

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"[Error processing image: {e}]"
