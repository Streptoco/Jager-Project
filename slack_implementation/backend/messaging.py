import json
import slack_sdk as slack
import os
from flask import Flask
from slackeventsapi import SlackEventAdapter as eventAdapter
import requests
import sys
sys.path.insert(0,'C:\\Users\\AfikAtias\\PycharmProjects\\Jager-Project\\jager-common')
import common-runtime
app = Flask(__name__)

eventAdapter = eventAdapter(os.environ['SLACK_SIGNING_SECRET'], '/slack/events', app)



bot = client.api_call("auth.test")['user_id']

# local ollama instance
chatUrl = 'http://localhost:11434/api/chat'
generateUrl = 'http://localhost:11434/api/generate'



@eventAdapter.on('message')
def onMessage(message):
    # print(message)
    event = message.get('event', {})
    channel = event.get('channel')
    user = event.get('user')
    responeUser = client.users_info(user=user)
    text = event.get('text')
    print(responeUser['user']['real_name'])
    if bot in text:
        botMessage = client.chat_postMessage(channel=channel,text="I'm Thinking...")
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
        response = requests.post(generateUrl, json=body)
        response_data = json.loads(response.text)
        print("FOR ME!")
        # content = response_data["message"]["content"]
        content = response_data["response"]
        #client.chat_postMessage(channel=channel,text=content)
        client.chat_update(channel=channel,ts=botMessage.get('ts'), text=content)

app.run(host='0.0.0.0', port=5000, debug=True)