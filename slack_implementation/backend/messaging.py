import json
import slack_sdk as slack
import os
from flask import Flask
from slackeventsapi import SlackEventAdapter as eventAdapter
import requests
from jager_common.slack_client import SlackClient
import messaging_parser

app = Flask(__name__)

eventAdapter = eventAdapter(os.environ['SLACK_SIGNING_SECRET'], '/slack/events', app)

#client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
#bot = client.api_call("auth.test")['user_id']
client = SlackClient()

# local ollama instance
chatUrl = 'http://localhost:11434/api/chat'
generateUrl = 'http://localhost:11434/api/generate'



@eventAdapter.on('message')
def onMessage(message):
    # print(message)
    event = message.get('event', {})
    channel = event.get('channel')
    text = event.get('text')
    print("Bot GUID:" + client.bot)
    print("Username: " + messaging_parser.get_real_name(message, client))
    print("Message: " + text)
    print(message)
    if "@"+client.bot in text:
        #botMessage = client.slack_client.chat_postMessage(channel=channel,text="I'm Thinking...")
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
        #client.slack_client.chat_update(channel=channel,ts=botMessage.get('ts'), text=content)
        client.slack_client.chat_postMessage(channel=channel,text=content)

app.run(host='0.0.0.0', port=5000, debug=True)