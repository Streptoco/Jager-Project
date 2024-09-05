import datetime
import os
import re

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)
event_adapter = SlackEventAdapter(os.environ['SLACK_SIGNING_SECRET'], '/slack/events', app)
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])


def fetch_all_messages(channel_map):
    message_map = {}
    for channel_id, channel_name in channel_map.items():  # Iterate over channel_map's items
        try:
            print(f"Fetching messages from channel: {channel_name} (ID: {channel_id})")  # Debugging info
            result = client.conversations_history(channel=channel_id)  # Use channel_id directly

            for msg in result['messages']:
                    message_map[msg.get('client_msg_id')] = (msg, channel_name)

            while result.get('has_more', False):  # Check if there are more messages
                result = client.conversations_history(
                    channel=channel_id,
                    cursor=result['response_metadata']['next_cursor']
                )
                for msg in result['messages']:
                    print(msg, channel_name)
                    message_map[msg.get('client_msg_id')] = (msg, channel_name)


        except SlackApiError as e:
            print(f"Error fetching conversations from {channel_name}: {e.response['error']}")

    return message_map


def fetch_user_info(user_id):
    try:
        response = client.users_info(user=user_id)
        return response['user']['name']
    except SlackApiError as e:
        print(f"Error fetching user info: {e.response['error']}")
        return user_id  # Fallback to user_id if there's an error


def get_user_mapping(messages):
    user_ids = set()
    for client_msg_id, (msg, channel_name) in messages.items():
        user_ids.add(msg.get('user'))

    user_mapping = {}
    for user_id in user_ids:
        if user_id:
            user_mapping[user_id] = fetch_user_info(user_id)

    return user_mapping


def replace_user_ids_with_names(messages_map, user_mapping):
    for client_msg_id, (msg, channel_name) in messages_map.items():
        user_id = msg.get('user')
        if user_id and user_id in user_mapping:
            print(msg['user'])
            msg['user'] = user_mapping[user_id]
            print(msg['user'])
        if 'text' in msg:
            msg['text'] = replace_text_user_ids(msg['text'], user_mapping)

    return messages_map


def replace_text_user_ids(text, user_mapping):
    def replace_match(match):
        user_id = match.group(1)
        return f"@{user_mapping.get(user_id, user_id)}"

    return re.sub(r'<@(\w+)>', replace_match, text)


def convert_messages_to_markdown(messages_map):
    markdown_content = ""
    for client_msg_id, (msg, channel_name) in messages_map.items():
        user = msg.get('user', 'unknown')
        text = msg.get('text', '')
        annoying_message = re.compile(r'afikat \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\)\nhi')
        if "jageragent" in text or "jageragentv2" in text or "This message was deleted" in text or annoying_message.search(text)\
                or "please read all new messages" in text or "has joined the channel" in text or "jageragentv2" in user or "jageragent" in user:
            continue
        timestamp = datetime.datetime.fromtimestamp(float(msg.get('ts', 0)))
        markdown_content += f"### \n {user} sent the following message: {text} in channel: {channel_name} at: ({timestamp})\n"
    return markdown_content


def save_markdown_to_file(content, filename):

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)


def fetch_all_channels():
    # Fetch channels and return a mapping of channel IDs to names
    channel_map = {}
    try:
        result = client.conversations_list()
        for channel in result['channels']:
            channel_map[channel['id']] = channel['name']
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
    return channel_map


def gather_and_save_messages():
    channel_map = fetch_all_channels()
    all_messages = fetch_all_messages(channel_map)
    user_mapping = get_user_mapping(all_messages)
    messages_with_names = replace_user_ids_with_names(all_messages, user_mapping)
    markdown_content = convert_messages_to_markdown(messages_with_names)
    directory = 'C:\\Users\\AfikAtias\\PycharmProjects\\Jager-Project\\slack_implementation\\backend'
    # Create the filename with the specified directory
    filename = os.path.join(directory, f"slack_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")

    save_markdown_to_file(markdown_content, filename)
    print(f"Saved messages to {filename}")


# Schedule the task
scheduler = BackgroundScheduler()
scheduler.add_job(gather_and_save_messages, 'interval', hours=3)
scheduler.start()

# Fetch and save messages once on startup
#gather_and_save_messages()

def get_real_name(message, client):
    event = message.get('event', {})
    user = event.get('user')
    responeUser = client.slack_client.users_info(user=user)
    return responeUser['user']['real_name']


def get_channel_real_name(message, client):
    event = message.get('event', {})
    channel = event.get('channel')
    responeUser = client.slack_client.conversations_info(channel=channel)
    return responeUser['channel']['name']

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
