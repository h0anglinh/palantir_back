from fastapi import APIRouter, HTTPException
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import os



router = APIRouter(prefix='/crm')

def create_ics_file( ):
        """
        Vytvoří .ics soubor pro událost.
        """
        ics_content = f"""BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:-//hacksw/handcal//NONSGML v1.0//EN
        BEGIN:VEVENT
        UID:20240410T103649Z@example.com
        DTSTAMP:20240410T103649Z
        DTSTART:20240411T103649
        DTEND:20240411T113649
        SUMMARY:Ukázková schůze
        DESCRIPTION:Diskuse o projektu
        LOCATION:Virtuální místnost
        END:VEVENT
        END:VCALENDAR
            """

        # Zapsání do dočasného souboru
        filename = "temp_pozvanka.ics"
        with open(filename, 'w') as file:
            file.write(ics_content)
        
        return filename

from icalendar import Calendar, Event, vCalAddress, vText
import tempfile
@router.get('/send/', tags=['crm'])
def send_email(summary: str, start: str):
    # Vytvoření kalendářní události
    cal = Calendar()
    cal.add('prodid', '-//Example Calendar//mxm.dk//')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', 'Phoenix Beauty')
    event.add('dtstart', datetime.now() + timedelta(days=1))
    event.add('dtend', datetime.now() + timedelta(days=1, hours=1))
    event.add('dtstamp', datetime.now())
    event['uid'] = '20230410T103649Z@example.com'
    organizer = vCalAddress('MAILTO:linh.hoang@hotmail.cz')
    organizer.params['cn'] = vText('Organizátor Schůzky')
    event['organizer'] = organizer
    event['location'] = vText('Chodska 13')

    cal.add_component(event)

    # Vytvoření dočasného souboru pro .ics soubor
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ics')
    temp_file.write(cal.to_ical())
    temp_file.close()

    # Nastavení e-mailu
    odesilatel = 'linh.hoang@phoenix-beauty.cz'
    prijemce = 'janapham90@hotmail.com'
    heslo = 'Sernato4'
    smtp_server = 'smtp.seznam.cz'
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = odesilatel
    msg['To'] = prijemce
    msg['Subject'] = "Pozvánka na schůzi"

    body = "Zde je pozvánka na Vaši nadcházející schůzi."
    msg.attach(MIMEText(body, 'plain'))

    with open(temp_file.name, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {os.path.basename(temp_file.name)}",
    )
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(odesilatel, heslo)
            server.sendmail(odesilatel, prijemce, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(temp_file.name)  # Odstranění dočasného souboru

    return {"message": "Pozvánka byla úspěšně odeslána."}