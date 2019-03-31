import os
import time
import re
import json
from slackclient import SlackClient

RTM_READ_DELAY= 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
COMMANDS = {}
messages = {}
slack_client = None

with open('token.txt') as token:
    slack_client = SlackClient(token.read().split('\n')[0])


with open('strings.json') as json_file:
    json_obj = json.load(json_file)
    COMMANDS = json_obj["commands"]
    messages = json_obj["en"]

bot_id = None

def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id:
                return message, event["channel"]

    return None, None


def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    # Default response is help text for the user
    default_response = messages["help"]
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(COMMANDS["start"]):
        response = messages["todo"]
    
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )



if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Bot running!")
        bot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                print("from: {}\nmessage: {}".format(channel, command))
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)

    else:
        print("Connection failed.")



