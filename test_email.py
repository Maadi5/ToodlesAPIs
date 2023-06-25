import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Sender's email address and password
sender_email = 'toodlesims@gmail.com'
#sender_password = 't00dle$DIGI'
sender_password = 'srdrejwluvndljqj'

# Recipient's email address
recipient_email = 'ausgphs@gmail.com'

# Create a message object
message = MIMEMultipart()
message['From'] = sender_email
message['To'] = recipient_email
message['Subject'] = 'Your email subject'

# Email content
body = 'This is the body of your email.'
message.attach(MIMEText(body, 'plain'))

# Establish a connection to the Gmail SMTP server
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
smtp_connection.starttls()

# Login to your Gmail account
print('logging in')
smtp_connection.login(sender_email, sender_password)

# Send the email
print('sending message')
smtp_connection.send_message(message)

# Close the connection
smtp_connection.quit()

