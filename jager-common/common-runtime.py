import os

import slack

client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])