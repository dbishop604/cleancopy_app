@app.route("/convert", methods=["POST"])
def convert():
    if "terms" not in request.form:
        flash("⚠️ You must agree to the terms of service and privacy policy before uploading.")
        return redirect(url_for("index"))

    if "fileUpload" not in request.files:
        flash("⚠️ No file selected")
        return redirect(url_for("index"))

    f = request.files["fileUpload"]
    if f.filename == "":
        flash("⚠️ No selected file")
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    base_name = filename.rsplit(".", 1)[0]

    temp_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(temp_path)

    try:
        text = process_file_to_text(temp_path, join_strategy="smart")
        fmt = request.form.get("format", "docx")

        if fmt == "txt":
            out_name = base_name + ".txt"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(text)
        else:
            out_name = base_name + ".docx"
            out_path = os.path.join(CONVERTED_FOLDER, out_name)
            buf = text_to_docx(text)
            with open(out_path, "wb") as out:
                out.write(buf.getbuffer())

        # redirect to success page with filename
        return redirect(url_for("success", file=out_name))

    except Exception as e:
        flash(f"❌ Conversion failed: {e}")
        return redirect(url_for("cancel"))
