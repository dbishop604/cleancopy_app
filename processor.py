import io
import os
import tempfile
import subprocess
from docx import Document
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

# --- Text extraction ---
def process_file_to_text(file_path, join_strategy="smart"):
    """
    Extract text from a file. Supports PDF, images (png/jpg/jpeg), and plain txt.
    join_strategy: "simple" joins lines with spaces, "smart" tries to preserve line breaks.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            parts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                parts.append(page_text)
            text = "\n\n".join(parts)
        except Exception as e:
            # fallback to pdftotext via poppler-utils
            try:
                result = subprocess.run(
                    ["pdftotext", file_path, "-"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                text = result.stdout.decode("utf-8", errors="ignore")
            except Exception as e2:
                raise RuntimeError(f"PDF extraction failed: {e2}")
