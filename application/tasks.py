from celery import Celery
from celery.schedules import crontab

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
import os
from email import encoders
from jinja2 import Template


import time
app=Celery('tasks',broker='redis://localhost:6379/0') 
app.conf.enable_utc=False
app.conf.timezone='Asia/Kolkata'

@app.on_after_configure.connect
def setup_periodic_tasks(sender,**kwargs):
    sender.add_periodic_task(10.0,add.s(2,4),name="dasdsa")
    sender.add_periodic_task(crontab(hour=7,minute=30,day_of_month=1),send_email.s("21f1007026@ds.study.iitm.ac.in", "Monthly report", "Please login to your account to view your monthly report",content='text',attachement_file=None),name="monthly mail")
    sender.add_periodic_task(10.0,send_email.s("21f1007026@ds.study.iitm.ac.in", "sending now", "message",content='text',attachement_file=None),name="10 seconds mail")
    # to send email every day at 8:00 AM 
    sender.add_periodic_task(crontab(minute=0, hour=8), send_email.s("21f1007026@ds.study.iitm.ac.in", "Remainder", "This is to remind you to check our latest offers",content='text',attachement_file=None),name="8:00 AM mail")
    


@app.task
def add(x,y):
    return x+y

@app.task
def send_email(to_address, subject, message,content='text',attachement_file=None):

    SMPTP_SERVER_HOST = 'smtp.gmail.com'
    SMPTP_SERVER_PORT = 587
    sender="nivedhaasrikanth@gmail.com"
    #recepient=sender
    SENDER_ADDRESS = sender
    SENDER_PASSWORD = 'igspycsgntvhlgas'
    print("calling send email")
    msg = MIMEMultipart()
    msg['From'] = SENDER_ADDRESS
    msg['To']=to_address
    msg['Subject'] = subject
    
    if content == 'html':
        msg.attach(MIMEText(message,'html'))
        
    else:
        msg.attach(MIMEText(message,'plain'))
        print("inside else")
    
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
        print("inside try")
        s = smtplib.SMTP(host=SMPTP_SERVER_HOST,port=SMPTP_SERVER_PORT)
        s.starttls()
        s.login(SENDER_ADDRESS,SENDER_PASSWORD)
        s.send_message(msg)
        s.quit()
        print("isntide mail sent")
        return True
    except Exception as e:
        print("inside except")
        print(e)
        return False
