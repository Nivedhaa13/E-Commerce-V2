from celery import Celery
from celery.schedules import crontab  
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os


import time
app=Celery('tasks',broker='redis://127.0.0.1:6379')
app.conf.enable_utc=False
app.conf.timezone='Asia/Kolkata'
attachments=['application/exports/orders.csv','application/exports/products.csv']
@app.on_after_configure.connect
def setup_periodic_tasks(sender,**kwargs):
    sender.add_periodic_task(10.0,add.s(1,2),name='add every 10')
    sender.add_periodic_task(30.0,print_s.s('hello'),name='print every 30')
    sender.add_periodic_task(
        crontab(hour=7,minute=30),
        send_email.s('nivedhaasrikanth@gmail.com','daily remainder','place your order for the day'),name='send email every monday')
    # to send every month 1st
    sender.add_periodic_task(
        crontab(hour=7,minute=30,day_of_month=1),
        send_email.s('nivedhaasrikanth@gmail.com','monthly summary','summary till date',attachments=attachments),name='send email every month')
    

@app.task
def add(x,y):
    print(x+y)
    return x+y

@app.task
def print_s(s):
    print(s)
    return s

@app.task
def send_email(recepient,subject,message,attachments=None):
    msg=MIMEMultipart()
    sender="nivedhaasrikanth@gmail.com"
    msg['From']=sender
    msg['To']=recepient
    msg['Subject']=subject
    msg.attach(MIMEText(message))

    if attachments:
        for filename in attachments:
            path = os.path.join(os.getcwd(), filename)
            with open(path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype="db")
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachment)


    smtp_server='smtp.gmail.com'
    smtp_port=587
    smtp_username=sender
    smtp_password="igspycsgntvhlgas"

    with smtplib.SMTP(smtp_server,smtp_port) as server:
        server.starttls()
        server.login(smtp_username,smtp_password)
        server.sendmail(sender,recepient,msg.as_string())




