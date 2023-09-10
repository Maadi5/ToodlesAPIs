import os
import requests
import json
from flask import Flask, request, jsonify
from gpt_base_v2 import GPT_Inference

from wati_apis import WATI_APIS

wati_triggers = WATI_APIS()
gpt_inference = GPT_Inference()
app = Flask(__name__)

def check_status(phone_number, whatsappMessageId):
    response_directory = "chatbot_response_tracker"
    filepath = os.path.join(response_directory, f"{phone_number}.txt")

    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            content = file.read().splitlines()
            if whatsappMessageId in content:
                print('\nDUPLICATE - already responded to', phone_number, whatsappMessageId,'\n')
                return True
            else:
                print('\nnot responded yet',phone_number, whatsappMessageId,'\n')
                return False
    else:
        print("\nphone number not present in chatbot_response_tracker",phone_number, whatsappMessageId,'\n')
        return False

def update_status(phone_number, whatsappMessageId):
    response_directory = "chatbot_response_tracker"
    filepath = os.path.join(response_directory, f"{phone_number}.txt")

    if not os.path.exists(filepath):
        with open(filepath, "w") as file:
            file.write(f"{whatsappMessageId}\n")
        print('\ncreated a new file in chatbot_response_tracker and updated the message ID')
    else:
        with open(filepath, "a") as file:
            file.write(f"{whatsappMessageId}\n")
        print('\nappended the message ID to chatbot_response_tracker')

@app.route('/wati_webhook', methods=['POST'])
def receive_wati_webhook():
    webhook_response = request.json
    print('\nwebhook response',webhook_response)
    phone_num = webhook_response['waId']
    text = webhook_response['text']
    wa_message_id = webhook_response['whatsappMessageId']
    print('\ntext received from user ',text)
    person_name = webhook_response['senderName']

    gpt_test_numbers = ['919176270768', '919445574311', '918754563901']

    if not check_status(phone_num, wa_message_id) and str(phone_num) in gpt_test_numbers:
        try:
            response = gpt_inference.get_response(phone_num, text)
            print('\nresponse:', str(response), 'contact number:', "'" + phone_num + "'", 'person name:', "'" + person_name + "'")
            wati_triggers.send_text_message_response(text_to_send=str(response), contact_number=str(phone_num), contact_name=str(person_name))
            print('\nsent response back to the user')
            update_status(phone_num, wa_message_id)
        except Exception as e:
            print(str(e))
            print('\nERROR send failed')
    elif str(phone_num) not in gpt_test_numbers:
        print("It's NOT the test number")
    else:
        print('\ncheck_status failed, duplicate message')
    return jsonify(webhook_response), 200

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True, port=5005)
