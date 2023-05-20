import os
import requests
import json
from flask import Flask, request, jsonify
from wati_apis import WATI_APIS

app = Flask(__name__)

wati = WATI_APIS()

#Swagger UI endpoint to accept phone number and message
@app.route('/send-whatsapp', methods=['GET', 'POST'])
def send_whatsapp():
    phone_number = str(request.json['contact-number'])
    person_name = str(request.json['contact-name'])
    message_template = str(request.json['message'])

    # WATI API call
    if not message_template:
        outcome = wati.send_template_message(contact_number=phone_number, contact_name =person_name)
    else:
        outcome = wati.send_template_message(contact_number=phone_number, contact_name=person_name, template_name=message_template)

    if outcome:
        status = 'Success'
    else:
        status = 'Failure'

    return jsonify({'status': status, 'response': {}}), 200

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True, port=5001)
