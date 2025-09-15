import os
from docx import Document
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from tempfile import TemporaryDirectory
from PIL import Image


def process_file_job(file_path, output_format="docx"):
    """
    Converts a scanned PDF into an editable DOCX file using OCR.

    Args:
        file_path (str): Path to the uploaded PDF file.
        output_format (str): Desired output format ("docx" supported).

    Returns:
        str: Path to the generated DOCX file.
    """
    if output_format.lower() != "docx":
        raise ValueError("❌ Only DOCX output is supported.")

    output_path = file_path.replace(".pdf", ".docx")
    text = ""

    # Try extracting text directly first
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    except Exception as e:
        print("⚠️ Error reading PDF directly:", e)

    # If no text found, fall back to OCR
    if not text.strip():
        print("🔎 No text found, switching to OCR...")
        with TemporaryDirectory() as tempdir:
            images = convert_from_path(file_path, output_folder=tempdir)
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"

    # Save extracted text into a DOCX
    doc = Document()
    doc.add_paragraph(text.strip() if text.strip() else "⚠️ No text could be extracted.")
    doc.save(output_path)

    print(f"✅ Processing complete. Saved to {output_path}")
    return output_path
