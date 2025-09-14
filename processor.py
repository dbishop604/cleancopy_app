import os
from docx import Document
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def process_file_job(input_path, output_path, job_id):
    """
    Convert a PDF to DOCX by running OCR on each page.
    Saves the result as a Word file.
    """

    doc = Document()
    doc.add_heading(f"Job ID: {job_id}", level=1)
    doc.add_paragraph(f"Source file: {os.path.basename(input_path)}")
    doc.add_paragraph("")

    # If it's a PDF, process with pdf2image
    if input_path.lower().endswith(".pdf"):
        try:
            pages = convert_from_path(input_path, dpi=300)
            for i, page in enumerate(pages, start=1):
                text = pytesseract.image_to_string(page)
                doc.add_heading(f"Page {i}", level=2)
                doc.add_paragraph(text.strip())
                doc.add_paragraph("")  # spacing
        except Exception as e:
            doc.add_paragraph(f"❌ Error during PDF OCR: {e}")
    else:
        # If it's an image (png/jpg), OCR it directly
        try:
            img = Image.open(input_path)
            text = pytesseract.image_to_string(img)
