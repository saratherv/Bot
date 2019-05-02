import json
from fb_messenger_server.consts import ACCESS_TOKEN
import requests


BUTTON_DATA = {
    "get_started": {
        "payload": "get_started_postback"
    },
    "persistent_menu": [
        {
            "locale": "default",
            "composer_input_disabled": False,
            "call_to_actions": [
                {
                    "title": "Log a Meal",
                    "type": "postback",
                    "payload": "meal"
                },
                {
                    "title": "Ask a Question",
                    "type": "postback",
                    "payload": "question"
                }
            ]
        }
    ]
}


def add_all_buttons():
    url = "https://graph.facebook.com/v2.6/me/messenger_profile?access_token={}".format(ACCESS_TOKEN)
    req = requests.post(url, data=json.dumps(BUTTON_DATA), headers={'Content-Type': 'application/json'})
    return req


if __name__ == "__main__":
    from pprint import pprint
    pprint(add_all_buttons().content)
