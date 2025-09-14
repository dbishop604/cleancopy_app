import os
import pytesseract
from pdf2image import convert_from_path
from docx import Document
from PIL import Image

UPLOAD_FOLDER = "/data/uploads"
OUTPUT_FOLDER = "/data/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def process_file(input_path: str, output_path: str):
    """
    Convert an uploaded PDF or image into a clean DOCX with OCR.
    """
    text_chunks = []

    # Handle PDF
    if input_path.lower().endswith(".pdf"):
        pages = convert_from_path(input_path)
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page)
            text_chunks.append(text)

    # Handle image files (JPG, PNG, TIFF)
    else:
        img = Image.open(input_path)
        text = pytesseract.image_to_string(img)
        text_chunks.append(text)

    # Write to DOCX
    doc = Document()
    for chunk in text_chunks:
        doc.add_paragraph(chunk.strip())
        doc.add_paragraph("")  # blank line between pages

    doc.save(output_path)

    return output_path
