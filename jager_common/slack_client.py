from slack_sdk import WebClient
import os


class SlackClient:
    def __init__(self):
        self.slack_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        self.bot = self.slack_client.api_call("auth.test")['user_id']
