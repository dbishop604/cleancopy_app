import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document

def process_file_to_text(filepath, join_strategy="smart"):
    """
    Convert a PDF or image file to extracted text using Tesseract OCR.
    Supports: PDF, JPG, PNG, TIFF.
    """
    text = ""

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        # Convert each page to image and OCR
        pages = convert_from_path(filepath)
        chunks = []
        for i, page in enumerate(pages):
            temp_img = f"/tmp/page_{i}.png"
            page.save(temp_img, "PNG")
            page_text = pytesseract.image_to_string(Image.open(temp_img))
            chunks.append(page_text.strip())
            os.remove(temp_img)

        if join_strategy == "smart":
            text = "\n\n".join(chunks)
        else:
            text = "\n".join(chunks)

    elif ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)

    else:
        raise ValueError("Unsupported file type. Please upload PDF, JPG, PNG, or TIFF.")

    return text.strip()


def text_to_docx(text, output_path=None):
    """
    Convert extracted text into a DOCX file.
    Returns a BytesIO if output_path is None, otherwise writes to disk.
    """
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)

    if output_path:
        doc.save(output_path)
        return output_path
    else
