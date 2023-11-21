import os
import requests
import json
from flask import Flask, request, jsonify
# from gpt_base_v2 import GPT_Inference
# from chat_tracking import chat_tracker
import time

from wati_apis import WATI_APIS

# chats = chat_tracker()
# wati_triggers = WATI_APIS()
# gpt_inference = GPT_Inference()
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

@app.route('/insta_webhook', methods=['POST'])
def receive_wati_webhook():
    webhook_response = request.json
    print('\nwebhook response',webhook_response)

    return jsonify(webhook_response), 200

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True, port=5005)
