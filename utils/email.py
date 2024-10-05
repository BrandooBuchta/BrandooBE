import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from typing import Optional

def getEmailHtml(title: str, subtitle: str, code: str = None):
    code_html = f"<strong style='font-size: 32px; color: white; padding: 20px 0px;'>{code}</strong>" if code else ""
    logo_url = "https://www.brandoo.cz/brandoo-logo-white.png"
    
    return f"""
            <div style="text-align: center; background: #006fee; padding: 20px;">
                <img src="{logo_url}" alt="Logo" style="width: 150px; height: auto; margin-bottom: 20px;" />
                <h1 style="font-size: 24px; margin: 0; color: white;">{title}</h1>
                <p style="margin: 5px 0; color: white;">{subtitle}</p>
                {code_html}
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

def send_free_subscription_on_month_email(email: str, code: str):
    subject = "Brandoo na měsíc zdarma!"
    body = getEmailHtml(
        'Vítejte, zde je váš unikátní kód pro váš bezstarostný měsíc zdarma.', 
        'Pokud byste měli problém s napojením na váš web, kontaktujte nás na info@brandoo.cz',
        code
    )
    send_email(subject, email, body)

def send_free_subscription_on_three_month_email(email: str, code: str):
    subject = "Brandoo na tři měsíce zdarma!"
    body = getEmailHtml(
        'Vítejte, zde je váš unikátní kód pro vaše bezstarostné tři měsíc ezdarma.', 
        'Jakmile bude vaše stránka hotová, napojíme vám na ní na Brandoo za již slíbenou jednu korunu.',
        code
    )
    send_email(subject, email, body)

def send_form_for_our_services(email: str):
    subject = "Brandoo Enterprises - Děkujeme že v nás vkládáte důvěru!"
    body = getEmailHtml(
        'Tady je odkaz na formulář, pomocí kterého lépe určíme co potřebujete a co vám my můžeme nabídnout abychom maximalizovali vaše výdělky.', 
        '<a href="https://www.brandoo.cz/form/b4766a43-bbe5-4ba2-86f3-13cc6e28d96c" target="_blank" style="color: white; font-weight: bold;">Klikni zde pro přesměrování na formulář!</a>',
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

def send_delete_user_email(email: str):
    subject = "Brandoo - Smazání vašeho účtu"
    body = getEmailHtml(
        'Smazání Vašeho Účtu', 
        'Váš účet byl smazán z důvodu neověření vaší identity.',
    )
    send_email(subject, email, body)
