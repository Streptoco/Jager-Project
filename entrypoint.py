import slack_sdk as slack
import os
from flask import Flask
from slackeventsapi import SlackEventAdapter as eventAdapter

app = Flask(__name__)

eventAdapter = eventAdapter(os.environ['SLACK_SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])

bot = client.api_call("auth.test")['user_id']

@eventAdapter.on('message')
def onMessage(message):
    print(message)
    event = message.get('event', {})
    channel = event.get('channel')
    user = event.get('user')
    text = event.get('text')
    if bot in text:
        print("FOR ME!")
        client.chat_postMessage(channel=channel,text="I don't have AI yet you greek goof")


app.run(host='0.0.0.0', port=5000, debug=True)