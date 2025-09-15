import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # Try extracting text using PyPDF2 first
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        text = text.strip()

        # If no text was found (i.e. it's a scanned PDF), fall back to OCR
        if not text:
            images = convert_from_path(pdf_path)
            for i, image in enumerate(images):
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


def process_file_job(file_path):
    try:
        # Output setup
        output_folder = "/data/output"
        os.makedirs(output_folder, exist_ok=True)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        output_file = os.path.join(output_folder, f"{name}.txt")

        # Determine file type
        ext = ext.lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", "]()
