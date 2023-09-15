from .workers import celery
from celery.schedules import crontab  
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging
from .database import *
from .models import *
from datetime import datetime, timedelta
from .mail import format_message, send_email
from jinja2 import Template
import pdfkit


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=7,minute=30,day_of_month=1), user_engagment.s(), name='Monthly Report')
    sender.add_periodic_task(crontab(minute=0, hour=0), daily_reminder.s(), name='daily reminders')

attachments=['./application/exports/orders.csv','./application/exports/products.csv','./application/exports/User_Order.csv']


@celery.task()
def daily_reminder():
    users = User.query.all()
    for user in users:
        last_activity = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.visit_date.desc()).first()

        if last_activity is None or (datetime.utcnow() - last_activity.visit_date) >= timedelta(days=1):
            data = {
                'username':user.username
            }
            message= format_message('frontend/daily_reminder.html',data=data)
            send_email(
                user.email,
                subject='Daily Reminder',
                message=message,
                content="html",
            )

@celery.task()
def user_engagment():
    users = User.query.all()
    for user in users:
        result = monthly_report.delay(user.id)


def format_report(template_file,user,month,item,year):
    with open(template_file) as file:
        template = Template(file.read())
        return template.render(user = user,month = month, item = item ,year=year)

@celery.task()
def monthly_report(user_id):
    user = User.query.filter_by(id = user_id).first()

    now = datetime.now()
    month = now.month
    year = now.year

    filtered_products = []
    for item in user.order:
        if item.order_date.month == month and item.order_date.year == year:
            filtered_products.append(item)

    file_html = format_report('frontend/monthly_report.html',user = user,month = month, item = filtered_products,year=year)
    filename = f'{user.username}_{month}_{year}.pdf'
    pdfkit.from_file(file_html, filename)
    send_email(
        user.email,
        subject=f"Monthly Engagement Report - {month}/{year}",
        message=file_html,
        content="html",
        attachments=[filename]
    )

@celery.task
def send_email(recepient, subject, message, attachments=None):
    msg = MIMEMultipart()
    sender = "nivedhaasrikanth@gmail.com"
    msg['From'] = sender
    msg['To'] = recepient
    msg['Subject'] = subject
    msg.attach(MIMEText(message))

    if attachments:
        for filename in attachments:
            path = os.path.join(os.getcwd(), filename)
            try:
                with open(path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype="csv")
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)
            except FileNotFoundError as e:
                logging.error(f"Attachment not found: {filename}")
            except Exception as e:
                logging.error(f"Error attaching {filename}: {str(e)}")

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = sender
    smtp_password = "igspycsgntvhlgas"

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender, recepient, msg.as_string())
