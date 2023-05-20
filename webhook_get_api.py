import os
import requests
import json
from flask import Flask, request, jsonify


app = Flask(__name__)

@app.route('/wati_webhook', methods=['GET'])
def receive_wati_webhook():
    webhook_response = request.json
    print(webhook_response)
    return jsonify(webhook_response), 200

if __name__ == '__main__':
    app.run(debug=True, port=5005)
