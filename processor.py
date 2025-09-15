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

        # If PDF is scanned (no text), use OCR
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


def process_file_job(file_path):
    try:
        output_folder = "/data/output"
        os.makedirs(output_folder, exist_ok=True)

        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        output_file = os.path.join(output_folder, f"{name}.txt")

        ext = ext.lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            text = extract_text_from_image(file_path)
        else:
            return f"Unsupported file type: {ext}"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text.strip() or "[No readable text found]")

        return os.path.basename(output_file)
    except Exception as e:
        return f"[Error processing file: {str(e)}]"
