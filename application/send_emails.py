
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
import os
from email import encoders
from jinja2 import Template

SMPTP_SERVER_HOST = 'nivedhaasrikanth@gmail.com'
SMPTP_SERVER_PORT = 587
sender="nivedhaasrikanth@gmail.com"
#recepient=sender
SENDER_ADDRESS = sender
SENDER_PASSWORD = 'igspycsgntvhlgas'


def send_email(to_address, subject, message,content='text',attachement_file=None):
    msg = MIMEMultipart()
    msg['From'] = SENDER_ADDRESS
    msg['To']=to_address
    msg['Subject'] = subject
    
    if content == 'html':
        msg.attach(MIMEText(message,'html'))
    else:
        msg.attach(MIMEText(message,'plain'))
    
    if attachement_file:
        with open(attachement_file,'rb') as attachment:
            part = MIMEBase('application','octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition', f'attachment; filemane={attachement_file}',
        )
        msg.attach(part)
    try:
        s = smtplib.SMTP(host=SMPTP_SERVER_HOST,port=SMPTP_SERVER_PORT)
        s.starttls()
        s.login(SENDER_ADDRESS,SENDER_PASSWORD)
        s.send_message(msg)
        s.quit()
        return True
    except:
        return False


def format_message(template_file,data={}):
    with open(template_file) as file:
        template = Template(file.read())
        return template.render(data=data)



#smtp_username=sender
#smtp_password="igspycsgntvhlgas"