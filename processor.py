import os
from docx import Document
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from tempfile import TemporaryDirectory


def process_file(file_path, output_format):
    """
    Converts a scanned PDF to an editable DOCX file using OCR.
    
    Args:
        file_path (str): Path to the uploaded PDF.
        output_format (str): Desired output format. Only 'docx' supported.

    Returns:
        str: Path to the output DOCX file.
    """
    if output_format.lower() != "docx":
        raise ValueError("Only DOCX output is currently supported.")

    text = ""

    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
        if not text.strip():
            raise ValueError("No text found in PDF, falling back to OCR.")
    except Exception:
        with TemporaryDirectory() as tempdir:
            images = convert_from_path(file_path, dpi=300, output_folder=tempdir)
            for img in images:
                text += pytesseract.image_to_string(img.convert("L"))

    document = Document()
    document.add_paragraph(text.strip())
    output_path = file_path.replace(".pdf", ".docx")
    document.save(output_path)

    return output_path
