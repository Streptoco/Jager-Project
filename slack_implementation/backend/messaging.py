import datetime
import json
import slack_sdk as slack
import os
from flask import Flask
from slackeventsapi import SlackEventAdapter as eventAdapter
import requests
from jager_common.chroma_db_listener import addToDB
from jager_common.slack_client import SlackClient
import messaging_parser
from main import *
from ollama import generate
import threading

app = Flask(__name__)
eventAdapter = eventAdapter(os.environ['SLACK_SIGNING_SECRET'], '/slack/events', app)
client = SlackClient()
lock = threading.Lock()

# local ollama instance
chatUrl = 'http://localhost:11434/api/chat'
generateUrl = 'http://localhost:11434/api/generate'
dbUrl = 'http://localhost:4090/'

@eventAdapter.on('message')
def onMessage(message):
    event = message.get('event', {})
    channel = event.get('channel')
    text = event.get('text')
    message_ts = event.get('ts')
    user_guid = event.get('user')
    user = messaging_parser.get_real_name(message, client)
    #in md file @jager and not @GUID
    if "@"+client.bot in text and user_guid != client.bot and client.check_if_can_send():
        lock.acquire()
        client.slack_client.chat_postMessage(channel=channel, text="Let me think...", thread_ts=message_ts)
        print("Bot GUID:" + client.bot)
        print("Username: " + user)
        print("User GUID: " + user_guid)
        print("Message: " + text)
        print("Message timestamp: " + message_ts)
        client.send_message()
        text = text.replace('<@' + client.bot + '>', '' + user + ': ')
        '''
        body = {
            "model": "llama3",
            "messages": [
                {
                    "role" : "user",
                    "content": text
                }
            ],
            "stream": False
        }
        '''
        body = {
            "model": "llama3",
            "prompt": text,
            "stream": False
        }
        #response = requests.post(generateUrl, json=body)
        #response_data = json.loads(response.text)
        print("FOR ME!")
        #content = response_data["message"]["content"]
        #content = response_data["response"]

        #Generate a respone based of nothing, just like a very stupid GPT
        #response = generate('llama3', text)
        #content = response['response']

        prompt_response = requests.get(dbUrl + 'queryDB' + '?prompt=' + text)
        content = json.loads(prompt_response.text)
        print("bot answer: " + content)
        client.slack_client.chat_postMessage(channel=channel, text=content, thread_ts=message_ts)
        client.post_sending()
        lock.release()
    elif user_guid != client.bot:
        channel_real_name = messaging_parser.get_channel_real_name(message, client)
        postToDatabaseBody = {
            "timestamp": message_ts,
            "user": user,
            "text": text,
            "channel": channel_real_name
        }
        add_to_db_response = requests.post(dbUrl + 'addToDB', json=postToDatabaseBody)
        add_to_db_response_data = json.loads(add_to_db_response.text)
        print("message added to db: " + add_to_db_response_data)
        return 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('fullchain.pem', 'privkey.pem'))

