import os
from flask import Flask, request, jsonify
from processor import process_file

app = Flask(__name__)


@app.route("/process", methods=["POST"])
def handle_process():
    if "file" not in request.files or "format" not in request.form:
        return jsonify({"error": "Missing file or format."}), 400

    uploaded_file = request.files["file"]
    output_format = request.form["format"]
    filename = uploaded_file.filename

    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    file_path = os.path.join("/tmp", filename)
    uploaded_file.save(file_path)

    try:
        output_path = process_file(file_path, output_format)
        return jsonify({"success": True, "output_path": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
