def get_real_name(message, client):
    event = message.get('event', {})
    user = event.get('user')
    responeUser = client.slack_client.users_info(user=user)
    return responeUser['user']['real_name']
