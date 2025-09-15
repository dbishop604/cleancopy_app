import os

def process_file_job(file_path):
    try:
        # Make sure output folder exists
        output_folder = "/data/output"
        os.makedirs(output_folder, exist_ok=True)

        # Read original file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple transformation (optional: can customize)
        processed_content = content.upper()  # Example: convert text to uppercase

        # Create output path
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_folder, f"processed_{filename}")

        # Write processed file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        return f"processed_{filename}"
    except Exception as e:
        return f"Error processing file: {str(e)}"
