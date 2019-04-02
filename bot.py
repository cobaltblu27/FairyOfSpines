import os
import time
import re
import json
from threading import Timer
from slackclient import SlackClient
from datetime import datetime, timedelta

RTM_READ_DELAY = 0.1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
COMMANDS = {}
MESSAGES = {}
CONFIGS = {}

with open('config.yml') as config_file:
    lines = [x.strip() for x in config_file.readlines()]
    for line in lines:
        key_val = line.split(": ")
        CONFIGS[key_val[0]] = key_val[1]


with open('strings.json') as json_file:
    json_obj = json.load(json_file)
    COMMANDS = json_obj["commands"]
    MESSAGES = json_obj[CONFIGS["Language"]]


class FairyOfSpine:
    slack_client = None
    bot_id = None
    time_dict = {}
    language = ""
    alarm_minutes = 60

    def __init__(self, configs):
        self.language = configs["Language"]
        self.alarm_minutes = configs["AlarmMinutes"]
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
        message_list = message.split("\\n")
        for message in message_list:
            response = self.slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=message
            )
        return response
                
    def update_message(self, channel, message, ts):
        message_list = message.split("\\n")
        for message in message_list:
            response = self.slack_client.api_call(
                "chat.update",
                channel=channel,
                text=message,
                ts=ts
            )
        return response

    def parse_time(self, command):
        #TODO: implement
        return {
            "next": None,
            "start_time": None,
            "end_time": None
        }

    def hour_later(self, time=datetime.now()):
        return time + timedelta(hours=1)

    def handle_command(self, command, channel):
        # Default response is help text for the user
        default_response = MESSAGES["help"]

        if command.startswith(COMMANDS["start"]):
            if channel in self.time_dict:
                self.send_message(channel, MESSAGES["already_on"])
            else:
                self.send_message(channel, MESSAGES["startup"])
                self.time_dict[channel] = {
                    "next": self.hour_later(),
                    "end_time": None
                }

        elif command.startswith(COMMANDS["stop"]):
            if channel not in self.time_dict:
                self.send_message(channel, MESSAGES["not_running"])
            else:
                self.send_message(channel, MESSAGES["turning_off"])
                self.time_dict.pop(channel)

        elif command.startswith(COMMANDS["auto"]):
            if channel in self.time_dict:
                self.send_message(channel, MESSAGES["stop_first"])
            else:
                self.send_message(channel, MESSAGES["startup_auto"])
                self.time_dict[channel] = self.parse_time(command)

        # Sends the response back to the channel
        else:
            self.send_message(channel, default_response)

    def _timeMessageThreadFunction(self, channel):
        for i in range(len(MESSAGES["stretch"])):
            if channel in self.time_dict:
                if MESSAGES["stretch"][i].startswith("COUNT"):
                    count = int(MESSAGES["stretch"][i].split()[1])
                    res = self.send_message(channel, "1")
                    for i in range(2, count + 1):
                        res = self.update_message(channel, str(i), res["ts"])
                        time.sleep(1)
                elif MESSAGES["stretch"][i].startswith("STOP"):
                    sleep_time = int(MESSAGES["stretch"][i].split()[1])
                    time.sleep(sleep_time)
                else:
                    self.send_message(channel, MESSAGES["stretch"][i])
                    time.sleep(1)

    def timeMessage(self, channel):
        t = Timer(0, lambda: self._timeMessageThreadFunction(channel))
        t.start()

    def checkTime(self):
        now = datetime.now()
        for key, val in self.time_dict.items():
            if val["end_time"] != None:
                if val["next"] < now:
                    next_time = self.hour_later()
                    if next_time > val["end_time"]:
                        next_time = self.hour_later(val["start_time"])
                    val["next"] = next_time
                    self.timeMessage(key)

            elif val["next"] < now:
                val["next"] = self.hour_later()
                self.timeMessage(key)

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
                # time.sleep(RTM_READ_DELAY)
        else:
            print("Connection failed")


if __name__ == "__main__":
    fs = FairyOfSpine(CONFIGS)
    fs.run()
