import os
from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, Response
from dotenv import load_dotenv
from urllib.parse import parse_qsl
from pprint import pprint
import json

load_dotenv('.env')

client = WebClient(os.environ.get('TOKEN'))
app = Flask(__name__)

def validate_webhook_token(payload: dict):
    if not 'token' in payload.keys():
        return 'No token provided'
    if not payload['token'] == os.environ.get('WEBHOOK_TOKEN'):
        return 'Incorrect token'
    return None

@app.route('/slack', methods=['POST'])
def slack_get_message():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.get_data())
    return Response(data['challenge'] if 'challenge' in data.keys() else 'Received', 200, headers={'Content-Type': 'plain-text'})

@app.route('/slack/send', methods=['POST'])
def slack_send_anon_message():
    content_type = request.headers.get('Content-Type')

    if content_type == 'application/json':
        req_data: dict = json.loads(request.get_data())
    elif content_type == 'application/x-www-form-urlencoded':
        req_data: dict = dict(parse_qsl(request.get_data(as_text=True), encoding='utf-8'))
    
    if err := validate_webhook_token(req_data):
        return Response(err, 401) # ToDo: change msg+success to error responses
    
    msg_split = req_data['text'].split(' ', 1)

    if len(msg_split) < 2:
        client.chat_postMessage(channel=req_data['channel_id'], text='Request failed. Invalid number of arguments')
        return Response('', 200) # ToDo: change msg+success to error responses

    channel, msg_text = msg_split[0], msg_split[1]

    try:
        client.chat_postMessage(channel=channel, text=msg_text)
    except SlackApiError:
        client.chat_postMessage(channel=req_data['channel_id'], text='Request failed. Please double-check channel name and try again')

    return Response('Message sent', 200)

@app.route('/', methods=['GET'])
def home():
    return Response('It kinda works', 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80')
