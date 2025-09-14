import pytesseract
from pdf2image import convert_from_path
from docx import Document

def process_file_to_text(input_path, join_strategy="smart"):
    """
    Convert PDF pages to text using OCR (pytesseract + pdf2image).
    """
    images = convert_from_path(input_path)
    texts = []
    for page_num, img in enumerate(images, start=1):
        text = pytesseract.image_to_string(img)
        if join_strategy == "smart":
            texts.append(f"--- Page {page_num} ---\n{text.strip()}")
        else:
            texts.append(text.strip())
    return "\n\n".join(texts)

def text_to_docx(text, output_path):
    """
    Save extracted text into a DOCX file.
    """
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(output_path)
    return output_path
