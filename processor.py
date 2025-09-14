import pytesseract
from pdf2image import convert_from_path
from docx import Document
from PIL import Image
import os

def process_file(input_path, output_path):
    text = ""

    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        pages = convert_from_path(input_path)
        for i, page in enumerate(pages):
            text += pytesseract.image_to_string(page) + "\n"
    elif ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
        img = Image.open(input_path)
        text = pytesseract.image_to_string(img)
    else:
        raise ValueError("Unsupported file type. Please upload PDF or image.")

    # Save as DOCX
    doc = Document()
    doc.add_paragraph(text.strip())
    doc.save(output_path)

    return output_path
