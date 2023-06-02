import os
import requests
import json
from flask import Flask, request, jsonify
from gpt_base import GPT_Inference

from wati_apis import WATI_APIS

wati_triggers = WATI_APIS()
gpt_inference = GPT_Inference()
app = Flask(__name__)

@app.route('/wati_webhook', methods=['POST'])
def receive_wati_webhook():
    webhook_response = request.json
    print(webhook_response)
    phone_num = webhook_response['waId']
    text = webhook_response['text']
    person_name = webhook_response['senderName']
    response = gpt_inference.get_response(text)

    try:
        print('response:', response, 'contact number:', "'" + phone_num + "'", 'person name:', "'" + person_name + "'")
        wati_triggers.send_text_message_response(text_to_send=response, contact_number=phone_num, contact_name=person_name)
    except:
        print('send failed')
    return jsonify(webhook_response), 200

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True, port=5005)
