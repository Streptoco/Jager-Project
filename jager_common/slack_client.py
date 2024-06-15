from slack_sdk import WebClient
import os


class SlackClient:
    def __init__(self):
        #self.slack_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        self.slack_client = WebClient(token="xoxb-6991111420352-7051339339906-H7yLGCZfWNk58OANngV0BFel")
        self.bot = self.slack_client.api_call("auth.test")['user_id']
        self.num_of_messages = 0

    def send_message(self):
        if self.num_of_messages == 0:
            self.num_of_messages += 1

    def post_sending(self):
        self.num_of_messages -= 1

    def check_if_can_send(self):
        if self.num_of_messages == 0:
            return True
        else:
            return False
