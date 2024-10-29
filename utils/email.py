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
                <h1 style="font-size: 24px; margin: 0; color: white;">{title}</h1>
                <p style="margin: 5px 0; color: white;">{subtitle}</p>
                <p style="margin: 5px 0; color: white;">{code_html}</p>
                <img src="{logo_url}" alt="Logo" style="width: 150px; height: auto; margin-bottom: 20px;" />
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

def send_thank_you(email: str):
    subject = "Brandoo Enterprises - Překvapení!"
    body = getEmailHtml(
        'Máme pro vás překvapení, napojíme vaší webovou stránku na Brandoo za 1 Kč!', 
        'Nemáte ještě webovou stránku? Můžete nás rovnou kontaktovat na info@brandoo.cz',
    )
    send_email(subject, email, body)

def send_form_for_our_services(email: str):
    subject = "Jeden dotazník vás dělí od úspěchu!"
    body = """
    <html>
        <body style="background-color: #ffffff; color: #000000;">
            <p>Zdravíme,</p>
            <p>
                děkujeme, že nám dáváte důvěru a rozhodli jste se zlepšit své podnikání s námi. 
                Připravili jsme pro vás formulář, pomocí kterého lépe zjistíme, co přesně potřebujete, 
                a co vám můžeme nabídnout, abychom maximalizovali vaše výdělky.
            </p>
            <p>
                Klikněte na následující odkaz, který vás přesměruje na formulář:
            </p>
            <p>
                <a href="https://www.brandoo.cz/form/924d28fc-f5ba-4e0c-8338-655cdf7ab794" target="_blank" 
                style="color: #0000ee; font-weight: bold;">Klikni zde pro přesměrování na formulář!</a>
            </p>
            <p>
                Děkujeme za váš zájem, těšíme se na spolupráci a na to, jak vám pomůžeme dosáhnout vašich cílů.
            </p>
            <p>S pozdravem, <br/>Tým Brandoo</p>
        </body>
    </html>
    """
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

def send_business_improvement_tip_email(email: str):
    subject = "Tip na zlepšení vašeho podnikání – Jak psát pro vyšší zisky"
    body = """
    <html>
        <body style="background-color: #ffffff; color: #000000;">
            <p>Zdravíme,</p>
            <p>
                děkujeme za váš zájem o náš tip! Hned se na něj vrhneme, protože jde o zásadní prvek, 
                který může okamžitě pozvednout vaše podnikání na další úroveň.
            </p>
            <p><strong>Tip, jak zlepšit vaše podnikání:</strong> Naučte se psát s cílem přenést emoce a přesvědčit.<br/>
                Váš text může být na webu, v emailu nebo v reklamě. Kvalitní copywriting prodává tím, 
                že u čtenáře vyvolá pocit, že mu rozumíte a nabízíte mu to, co potřebuje.</p>
            <p><strong>Jak na to:</strong></p>
            <ul>
                <li>Prozkoumejte svého ideálního klienta – Text bude účinnější, když budete mluvit přímo k jeho potřebám a snům.</li>
                <li>Vložte emoce – Neprodávejte jen produkt, ale to, jak se váš klient bude cítit, když jej získá.</li>
                <li>Udržujte přímočarost a jasnost – Každé slovo by mělo směřovat k hlavní myšlence.</li>
            </ul>
            <p>
                Pokud se vám nechce nebo nemáte čas, můžeme se o váš obsah postarat my. Ušetříte čas, dostanete kvalitní text na míru, 
                a můžete se plně věnovat růstu svého podnikání.
            </p>
            <p>Děkujeme za váš zájem a těšíme se na to, jak vám pomůžeme zlepšit vaše podnikání!</p>
            <p>S pozdravem, <br/>Tým Brandoo</p>
        </body>
    </html>
    """
    send_email(subject, email, body)

def send_extra_tip_video_email(email: str):
    subject = "Extra tip – Zvyšte účinnost textů pomocí videa"
    body = """
    <html>
        <body style="background-color: #ffffff; color: #000000;">
            <p>Zdravíme,</p>
            <p>
                jak jsme slíbili, máme pro vás ještě překvapení, extra tip navíc který zvýší účinnost vašich textů a podpoří váš byznys.
            </p>
            <p><strong>Extra tip:</strong> Natočte video a spojte své texty se svou tváří.<br/>
                Video je jedním z nejúčinnějších způsobů, jak zaujmout publikum. Převedení textu na video zvyšuje proklikovost a konverzi, protože:
            </p>
            <ul>
                <li><strong>Lidé milují vizuální obsah</strong> – Video je jednodušší a rychlejší na vnímání než dlouhý text.</li>
                <li><strong>Předáváte autentický dojem</strong> – Když vás divák uvidí, vytvoří si k vám vztah a důvěru.</li>
                <li><strong>Emoce a příběh</strong> – Videa lépe přenášejí emoce, a jak víme, právě emoce prodávají.</li>
            </ul>
            <p>
                Zvažte propojení videa s vašimi texty – ať už jde o příběh vaší značky, představení produktů nebo sdílení úspěchů.
            </p>
            <p>
                Pokud si na to netroufáte, jsme tu, abychom vám pomohli. Můžeme pro vás vytvořit silné texty i videa, 
                která budou reprezentovat vaši značku a zvýší vaši konverzi.
            </p>
            <p>Děkujeme, že jste s námi, a těšíme se na vaše úspěchy!</p>
            <p>S pozdravem, <br/>Tým Brandoo</p>
        </body>
    </html>
    """
    send_email(subject, email, body)
