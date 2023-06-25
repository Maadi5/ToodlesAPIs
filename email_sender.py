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

def send_dispatch_email(name, awb_number, to_address):
    sender_email = 'toodlesims@gmail.com'
    sender_password = config.gmail_key

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = to_address
    email_message['Subject'] = 'Toodles: Your order is dispatched!'

    message = 'Hi ' + name + '!\n' + \
              "We're thrilled to inform you that your long-awaited pre-ordered Toodles furniture is now ready to be dispatched!✨\n\n" + \
              "Here's the Bluedart tracking number for your order: " + awb_number + '\n' + \
              '(You can track your order at https://www.bluedart.com/tracking)\n'  + '\n' + \
              'If you have any questions or need further assistance, feel free to reach out to our customer support team.\n' + \
              'Thank you for choosing Toodles :)\n' + '\n' + \
              'Yours truly,\n' + 'Team Toodles'

    email_message.attach(MIMEText(message, 'plain'))

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
    smtp_connection.starttls()

    try:
        smtp_connection.login(sender_email, sender_password)
        smtp_connection.send_message(email_message)
        smtp_connection.quit()
        return "Success"

    except Exception as e:
        print(f"An error occurred while sending the email: {str(e)}")
        return "Failure"
