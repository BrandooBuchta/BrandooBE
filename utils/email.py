import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

def getEmailHtml(title: str, subtitle: str, code: str):
    return f"""
            <div style="text-align: center; background: #006fee; padding: 20px;">
                <h1 style="font-size: 24px; margin: 0; color: white;">{title}</h1>
                <p style="margin: 5px 0; color: white;">{subtitle}</p>
                <strong style="font-size: 32px; color: white; padding: 20px 0px;">{code}</strong>
                <div style="color: white;">{'no logo yet :P'}</div>
            </div>
        """

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(subject: str, recipient: str, body: str):
    sender_email = EMAIL_ADDRESS
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP('wes1-smtp.wedos.net', 587)
        server.starttls()
        server.login(sender_email, EMAIL_PASSWORD)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.close()
    except Exception as e:
        print(f"Error sending email: {e}")

def send_verification_email(email: str, code: str):
    subject = "Brandoo - Verifikace uživatele"
    body = getEmailHtml(
        'Verifikace Uživatele', 
        'Zde je kód pro verifikaci, nesdílejte tento kód s nikým.',
        code
    )
    send_email(subject, email, body)

def send_reset_email(email: str, code: str):
    subject = "Brandoo - Změna hesla"
    body = getEmailHtml(
        'Změna Hesla', 
        'Zde je kód pro změnu hesla, nesdílejte tento kód s nikým.',
        code
    )
    send_email(subject, email, body)

def send_delete_user_email(email: str, code: str):
    subject = "Brandoo - Smazání vašeho účtu"
    body = getEmailHtml(
        'Smazání Vašeho Účtu', 
        'Váš účet byl smazán z důvodu neověření vaší identity.',
        code
    )
    send_email(subject, email, body)
