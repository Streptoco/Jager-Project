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
    messages = []
    for channel in channel_map:
        try:
            result = client.conversations_history(channel=channel['id'])
            messages.extend(result['messages'])

            while result['has_more']:
                result = client.conversations_history(
                    channel=channel['id'],
                    cursor=result['response_metadata']['next_cursor']
                )
                messages.extend(result['messages'])

        except SlackApiError as e:
            print(f"Error fetching conversations: {e.response['error']}")

    return messages


def fetch_user_info(user_id):
    try:
        response = client.users_info(user=user_id)
        return response['user']['name']
    except SlackApiError as e:
        print(f"Error fetching user info: {e.response['error']}")
        return user_id  # Fallback to user_id if there's an error


def get_user_mapping(messages):
    user_ids = set()
    for msg in messages:
        user_ids.add(msg.get('user'))

    user_mapping = {}
    for user_id in user_ids:
        if user_id:
            user_mapping[user_id] = fetch_user_info(user_id)

    return user_mapping


def replace_user_ids_with_names(messages, user_mapping):
    for msg in messages:
        user_id = msg.get('user')
        if user_id and user_id in user_mapping:
            msg['user'] = user_mapping[user_id]
        if 'text' in msg:
            msg['text'] = replace_text_user_ids(msg['text'], user_mapping)
    return messages


def replace_text_user_ids(text, user_mapping):
    def replace_match(match):
        user_id = match.group(1)
        return f"@{user_mapping.get(user_id, user_id)}"

    return re.sub(r'<@(\w+)>', replace_match, text)


def convert_messages_to_markdown(messages, channel_map):
    markdown_content = ""
    for msg in messages:
        user = msg.get('user', 'unknown')
        text = msg.get('text', '')
        channel_id = msg.get('channel', 'unknown')
        channel_name = channel_map.get(channel_id, 'unknown channel')  # Lookup channel name
        print(f"channel name fetched: {channel_name}")
        annoying_message = re.compile(r'afikat \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\)\nhi')
        if "jageragent" in text or "jageragentv2" in text or "This message was deleted" in text or annoying_message.search(text)\
                or "please read all new messages" in text or "has joined the channel" in text or "jageragentv2" in user or "jageragent" in user:
            continue
        timestamp = datetime.datetime.fromtimestamp(float(msg.get('ts', 0)))
        #print(f"### {user} ({timestamp}) @{channel}\n{text}\n\n")
        markdown_content += f"### {user} ({timestamp})\n{text}\n\n"
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
    markdown_content = convert_messages_to_markdown(messages_with_names, channel_map)
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
