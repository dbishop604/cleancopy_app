import os
from docx import Document
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from tempfile import TemporaryDirectory
from PIL import Image


def process_file(file_path, output_format):
    """
    Converts a scanned PDF to an editable DOCX file using OCR.
    
    Args:
        file_path (str): The path to the uploaded PDF file.
        output_format (str): The desired output format (only 'docx' supported for now).
        
    Returns:
        output_path (str): The path to the generated file.
    """
    if output_format.lower() != "docx":
        raise ValueError("Only DOCX output is currently supported.")

    text = ""

    try:
        # Try reading text directly (in case it's a readable PDF)
        reader = PdfReader(file_path)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
        
        if text.strip():
            print("Text extracted without OCR.")
        else:
            raise Exception("No text found — switching to OCR
