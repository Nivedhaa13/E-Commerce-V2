import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

sender="nivedhaasrikanth@gmail.com"
recepient=sender
subject="test mail"
message="hello"

msg=MIMEMultipart()
msg['From']=sender
msg['To']=recepient
msg['Subject']=subject
msg.attach(MIMEText(message))


filename='models.py'
path=os.path.join(os.getcwd(),filename)
with open(path,'rb') as f:
    attachment=MIMEApplication(f.read(),_subtype="py")
    attachment.add_header('Content-Disposition','attachment',filename=filename)
    msg.attach(attachment)

smtp_server='smtp.gmail.com'
smtp_port=587
smtp_username=sender
smtp_password="igspycsgntvhlgas"

with smtplib.SMTP(smtp_server,smtp_port) as server:
    server.starttls()
    server.login(smtp_username,smtp_password)
    server.sendmail(sender,recepient,msg.as_string())
