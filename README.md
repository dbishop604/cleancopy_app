# CleanCopy OCR — MVP

Turn any PDF or image (scans, photos) into **continuous, editable text** and export as Word (.docx) or plain text (.txt). Designed to avoid the "broken chunks" you get from many converters.

> © Debbie Bishop. All rights reserved. Do not scrape, index, or redistribute.

---

## Features
- Upload **PDF** or **image** (PNG/JPG/TIFF/BMP)
- OCR via **Tesseract**
- **Smart line-joining** to merge artificial line breaks while keeping true paragraphs
- Export to **DOCX** or **TXT**
- Simple web UI

---

## Quick Start

### 0) Install system dependencies
- **Tesseract OCR**
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - macOS: `brew install tesseract`
  - Linux (Debian/Ubuntu): `sudo apt-get install tesseract-ocr`
- **Poppler** (for PDF → image conversion via `pdf2image`)
  - Windows: https://github.com/oschwartz10612/poppler-windows/releases/
    - Add `poppler-XX/bin` folder to your PATH
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`

> If you want to avoid Poppler, you can later swap `pdf2image` for PyMuPDF. Keeping this MVP simple.

### 1) Create & activate a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2) Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the app
```bash
export FLASK_SECRET_KEY="change-me"  # optional
python app.py
```
Open http://localhost:5000

---

## How It Works
1. **PDF → images** at 300 DPI (via `pdf2image` + Poppler)
2. **OCR** each page using Tesseract (`--psm 6`)
3. **Reflow** text with smart heuristics:
   - Remove artificial line breaks
   - Fix hyphenation at line endings
   - Keep blank lines as true paragraph breaks
4. **Export** to DOCX (via `python-docx`) or TXT

### Join Strategies
- **Smart (default)**: conservative, context-aware merging
- **Aggressive**: strip most single line breaks; keep only double as paragraphs
- **None**: raw OCR output

---

## CLI (Optional)
You can also import `processor.py` to run conversions programmatically:

```python
from processor import process_file_to_text, text_to_docx

text = process_file_to_text("input.pdf", join_strategy="smart")
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(text)

docx_buf = text_to_docx(text)
with open("output.docx", "wb") as f:
    f.write(docx_buf.read())
```

---

## Packaging & Distribution

### Option A: Ship as a simple **desktop app** (Electron wrapper)
- Keep this Flask server as the backend (localhost)
- Build a tiny Electron UI that loads `http://localhost:5000`
- Package with **Tesseract** and **Poppler** installers or provide a one-time setup guide

### Option B: **Web SaaS**
- Host Flask on a VM (e.g., Render, Fly.io, AWS EC2) *with* Tesseract + Poppler installed
- Add user auth, rate limits, and a queue for large files
- Monetize with Stripe subscriptions
- Add storage (S3/GCS) for temporary files and purging policy

### Option C: **Docker**
Ship a container image with everything pre-installed (see Dockerfile below).

---

## Docker (Optional)

```Dockerfile
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PORT=5000
CMD ["python", "app.py"]
```

Build & run:
```bash
docker build -t cleancopy-ocr .
docker run -it --rm -p 5000:5000 cleancopy-ocr
```

---

## Roadmap
- Detect headings/lists/tables more accurately
- Optional **AI re-paragraphing** for messy scans
- Batch mode + ZIP downloads
- Google Drive / Dropbox import
- Enterprise API

---

## License
This MVP is provided for your internal evaluation and distribution by Debbie Bishop. If you plan to open-source, we can add an MIT license instead.
