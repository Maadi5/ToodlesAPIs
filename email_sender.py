import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
import config
from datetime import datetime as d
import mimetypes

def send_email(message, subject, to_address):
    sender_email = 'operations@toodles.in'
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
    sender_email = 'operations@miniture.in'
    sender_password = config.gmail_key

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = to_address
    email_message['Subject'] = 'Toodles: Track your product'

    message = '<html><body><div style="font-family:verdana;overflow:auto"><p><pre>Hi ' + name + '!\n' + \
              "We're thrilled to inform you that your Toodles furniture is now ready to be dispatched!✨\n\n" + \
              "Here's the Bluedart tracking number for your order: " + awb_number + '\n' + \
              '(You can track your order at https://www.bluedart.com/tracking)\n'  + '\n' + \
              'If you have any questions or need further assistance, feel free to reach out to our customer support team.\n' + \
              'Thank you for choosing Toodles :)\n' + '\n' + \
              'Yours truly,\n' + 'Team Toodles</pre></p></div></body></html>'

    email_message.attach(MIMEText(message, 'html'))

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

def send_usermanual_email(name, product_name, product_manual_link, to_address):
    try:
        sender_name = 'Miniture (Formerly Toodles)'
        sender_email = 'operations@miniture.in'
        sender_password = config.gmail_key

        email_message = MIMEMultipart()
        email_message['From'] = formataddr((sender_name, sender_email))#sender_email
        email_message['To'] = to_address
        email_message['Subject'] = 'Toodles: ' + product_name + '- Assembly Guide'

        message = 'Hi ' + name + '!\n' + \
                  "This is Miniture (formerly Toodles).\n\n" + \
                  'Here is the installation manual for assembling your ' + product_name + ': ' + '<a href="' + product_manual_link + '">click here</a>\n\n' + \
                  "Feel free to ask us here if you have any queries. 📞\n\n" + \
                  'Yours truly,\n' + 'Team Toodles'

        message_html = '<body style=”font-family: Georgia !important;”><pre>Hi ' + name + '!\n' + \
                'Here is the installation manual for assembling your ' + product_name + ' :' + ' <a href="' + product_manual_link + '">click here</a>\n\n' + \
                "Feel free to ask us here if you have any queries. 📞\n\n" + \
                'Yours truly,\n' + 'Team Miniture (Formerly Toodles)</pre></body>'

        email_message.attach(MIMEText(message_html, 'html'))

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

    except Exception as e:
        print('email send error main loop: ', {str(e)})
        return "Failure"

def send_dispatch_usermanual_email(name, product_name, product_manual_link, to_address, awb_number):
    sender_email = 'operations@toodles.in'
    sender_password = config.gmail_key

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = to_address
    email_message['Subject'] = 'Toodles: Your order is dispatched'

    
    message = '<html><body><div style="font-family:verdana;overflow:auto"><p>Hi ' + name + '!\n' + \
              "We're thrilled to inform you that your long-awaited pre-ordered Toodles furniture is now ready to be dispatched!✨\n\n" + \
              "Here's the Bluedart tracking number for your order: " + awb_number + '\n' + \
              '(You can track your order at https://www.bluedart.com/tracking)\n'  + '\n' + \
              'Please find the user manual for your product with step-be-step assembly instructions here: <a href="' + product_manual_link + '">click here</a>\n' + \
              'If you have any questions or need further assistance, feel free to reach out to our customer support team.\n' + \
              'Thank you for choosing Toodles :)\n' + '\n' + \
              'Yours truly,\n' + 'Team Toodles</p></div></body></html>'

    email_message.attach(MIMEText(message, 'html'))

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



def send_csv(csvfile, subject='order_report'):
    sender_email = 'operations@toodles.in'
    sender_password = config.gmail_key

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    date_time = d.now()
    date_time = date_time.strftime("%d/%m/%Y")
    if subject == 'order_report':
        email_message['Subject'] = 'Daily Order Report for ' + str(date_time)
        email_message['To'] = 'finance@miniture.in'
    elif subject == 'incomplete_orders':
        email_message['Subject'] = 'Incomplete Orders for ' + str(date_time)
        email_message['To'] = sender_email
    elif subject == 'cancelled_orders':
        email_message['Subject'] = 'New Cancellations ' + str(date_time)
        email_message['To'] = 'finance@miniture.in'

    
    message = 'PFA Daily Report'

    email_message.attach(MIMEText(message, 'text'))
    ctype, encoding = mimetypes.guess_type(csvfile)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)

    if maintype == "text":
        fp = open(csvfile)
        # Note: we should handle calculating the charset
        attachment = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == "image":
        fp = open(csvfile, "rb")
        attachment = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == "audio":
        fp = open(csvfile, "rb")
        attachment = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(csvfile, "rb")
        attachment = MIMEBase(maintype, subtype)
        attachment.set_payload(fp.read())
        fp.close()
        encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=csvfile)
    email_message.attach(attachment)

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

if __name__ == '__main__':
    from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
    import traceback
    import os
    incomplete_csv_path = os.path.join(os.getcwd(), 'incomplete_csv.csv')
    #if incomplete_csv is not None:
    # incomplete_csv.to_csv(incomplete_csv_path, index= False)
    ## send csv email for incomplete orders
    try:
        status = send_csv(csvfile=incomplete_csv_path, subject='incomplete_orders')
        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
        # trackerdf.at[idx, 'email_status'] = status
        # email_status = status
    except:
        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
        # trackerdf.at[idx, 'email_status'] = 'Failure_exception'
        # email_status = 'Failure_exception'
        print('email csv failed: ', traceback.format_exc())