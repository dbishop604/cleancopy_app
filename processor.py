import os
from docx import Document
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def process_file_job(input_path, output_path, job_id):
    doc = Document()
    doc.add_heading(f"Job ID: {job_id}", level=1)
    doc.add_paragraph(f"Original file: {os.path.basename(input_path)}")

    try:
        if input_path.lower().endswith(".pdf"):
            # Convert PDF to images (one per page)
            pages = convert_from_path(input_path)
            for i, page in enumerate(pages, start=1):
                text = pytesseract.image_to_string(page)
                doc.add_heading(f"Page {i}", level=2)
                doc.add_paragraph(text.strip() or "[No text detected]")
        else:
            # Assume it's an image (jpg, png, tiff)
            img = Image.open(input_path)
            text = pytesseract.image_to_string(img)
            doc.add_paragraph(text.strip() or "[No text detected]")

    except Exception as e:
        doc.add_heading("Error during processing", level=2)
        doc.add_paragraph(str(e))

    # Save result
    doc.save(output_path)
    return output_path
