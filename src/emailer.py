from email.message import EmailMessage
from pathlib import Path
import smtplib

def send_report(username, app_password, recipient, subject, text_body, html_body, attachments,
                host="smtp.gmail.com", port=587):
    if not username or not app_password or not recipient:
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = username
    message["To"] = recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    for path in attachments:
        file_path = Path(path)
        if file_path.exists():
            subtype = "html" if file_path.suffix.lower() == ".html" else "csv" if file_path.suffix.lower() == ".csv" else "plain"
            maintype = "text"
            message.add_attachment(file_path.read_bytes(), maintype=maintype, subtype=subtype,
                                   filename=file_path.name)
    with smtplib.SMTP(host, port, timeout=35) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, app_password.replace(" ", ""))
        server.send_message(message)
    return True
