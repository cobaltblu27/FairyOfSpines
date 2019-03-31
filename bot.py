import os
import time
import re
import json
from threading import Timer
from slackclient import SlackClient

RTM_READ_DELAY= 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
COMMANDS = {}
MESSAGES = {}


with open('strings.json') as json_file:
    json_obj = json.load(json_file)
    COMMANDS = json_obj["commands"]
    MESSAGES = json_obj["en"]


class FairyOfSpine:
    slack_client = None
    bot_id = None
    active_channels = set()

    def __init__(self):
        with open('token.txt') as token:
            self.slack_client = SlackClient(token.read().split('\n')[0])

    def parse_bot_commands(self, slack_events):
        for event in slack_events:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = self.parse_direct_mention(event["text"])
                if user_id == self.bot_id:
                    return message, event["channel"]
        return None, None   

    def parse_direct_mention(self, message_text):
        matches = re.search(MENTION_REGEX, message_text)
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def send_message(self, channel, message):
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=message
        )

    def handle_command(self, command, channel):
        # Default response is help text for the user
        default_response = MESSAGES["help"]
        # Finds and executes the given command, filling in response
        response = None
        # This is where you start to implement more commands!
        if command.startswith(COMMANDS["start"]):
            if channel in self.active_channels:
                self.send_message(channel, MESSAGES["already_on"])
            else:
                self.send_message(channel, MESSAGES["startup"])
                self.active_channels.add(channel)

        elif command.startswith(COMMANDS["stop"]):
            if channel not in self.active_channels:
                self.send_message(channel, MESSAGES["not_running"])
            else:
                self.send_message(channel, MESSAGES["turning_off"])
                self.active_channels.discard(channel)

        elif command.startwith(COMMANDS["auto"]):
            pass
    
        # Sends the response back to the channel
        else:
            self.send_message(channel, response or default_response)
    
    def checkTime(self):
        pass
    
    def run(self):
        if self.slack_client.rtm_connect(with_team_state=False):
            print("Bot running!")
            self.bot_id = self.slack_client.api_call("auth.test")["user_id"]
            while True:
                command, channel = self.parse_bot_commands(
                    self.slack_client.rtm_read()
                )
                if command:
                    print("from: {}\nmessage: {}".format(channel, command))
                    self.handle_command(command, channel)
                self.checkTime()
                time.sleep(RTM_READ_DELAY)
        else:
            print("Connection failed")


if __name__ == "__main__":
    fs = FairyOfSpine()
    fs.run()



