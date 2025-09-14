from docx import Document

def process_file_job(input_path, output_path, job_id):
    # Placeholder conversion — replace with OCR later
    doc = Document()
    doc.add_heading(f"Job ID: {job_id}", level=1)
    doc.add_paragraph("This is a placeholder DOCX file created from your upload.")
    doc.add_paragraph(f"Original file: {input_path}")
    doc.save(output_path)
    return output_path
