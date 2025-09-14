from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ... your existing code ...

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("⚠️ Please fill out all fields.", "error")
            return redirect(url_for("contact"))

        try:
            # Email setup
            sender_email = "noreply@seamlessdocs.com"   # masked sender
            receiver_email = "admin@bystorytellers.online"
            subject = f"New Contact Form Submission from {name}"

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject

            body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            msg.attach(MIMEText(body, "plain"))

            # Use local SMTP (Render supports SendGrid, Postmark, etc.)
            # Replace with your email provider credentials if needed
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587) as server:  # example using Gmail
                server.starttls(context=context)
                server.login("your-gmail@gmail.com", "your-app-password")
                server.sendmail(sender_email, receiver_email, msg.as_string())

            flash("✅ Your message has been sent. Thank you!", "success")
            return redirect(url_for("contact"))

        except Exception as e:
            flash(f"❌ Error sending message: {e}", "error")
            return redirect(url_for("contact"))

    return render_template("contact.html")
