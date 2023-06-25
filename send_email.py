import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(message, subject, to_address):
    sender_email = 'toodlesims@gmail.com'
    sender_password = config.gmail_key

    #message object
    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = to_address
    email_message['Subject'] = subject

    body = message
    email_message.attach(MIMEText(body, 'plain'))

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
    smtp_connection.starttls()

    #login
    smtp_connection.login(sender_email, sender_password)

    #sending mail
    smtp_connection.send_message(email_message)

    smtp_connection.quit()

