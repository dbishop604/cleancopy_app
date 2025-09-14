import os
import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from docx import Document

def process_file_to_text(file_path, join_strategy="smart"):
    """
    Extract text from a PDF or image file.
    Supports PDF, JPG, JPEG, PNG, TIFF.
    """
    text_output = []

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in [".pdf"]:
            pages = convert_from_path(file_path)
            for page in pages:
                page_text = pytesseract.image_to_string(page)
                text_output.append(page_text.strip())
        elif ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            image = Image.open(file_path)
            page_text = pytesseract.image_to_string(image)
            text_output.append(page_text.strip())
        else:
            raise ValueError("Unsupported file type. Please upload PDF, JPG, PNG, or TIFF.")
    except Exception as e:
        raise RuntimeError(f"Error processing file: {e}")

    if join_strategy == "smart":
        return "\n\n".join([p for p in text_output if p])
    else:
        return "\n".join(text_output)

def text_to_docx(text: str) -> io.BytesIO:
    """
    Convert plain text into a DOCX document and return as a BytesIO buffer.
    The worker or web app can save this buffer to disk or stream it.
    """
    doc = Document()
