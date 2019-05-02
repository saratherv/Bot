from flask import request
import requests
import re

from fb_messenger_server import db, config
from fb_messenger_server.consts import FB_ENDPOINT, VERIFY_TOKEN, ACCESS_TOKEN
from fb_messenger_server import logger
from fb_messenger_server.hop_client import HopClient


PHONE_PATTERN = re.compile("(0/91)?[7-9][0-9]{9}")
USER_URL_PATTERN = "https://graph.facebook.com/{psid}?fields=first_name,last_name,profile_pic,gender,timezone&access_token={access_token}"
MEAL_MODE = 'meal'
QUESTION_MODE = 'question'


def handle_verification():
    if request.args['hub.verify_token'] == VERIFY_TOKEN:
        return request.args['hub.challenge']
    else:
        return "Invalid verification token"


def fb_get_user(psid):
    url = USER_URL_PATTERN.format(psid=psid, access_token=ACCESS_TOKEN)
    try:
        resp = requests.get(url)
        data = resp.json()
    except BaseException as e:
        logger.error("could not get fb user data because {}".format(e))
        raise e
    if not resp.ok:
        raise Exception("could not get fb user data, got result {0} {1}".format(data.status, data.content))
    logger.info("requesting fb user: {}".format(data))
    return data


class User(object):
    def __init__(self, data):
        self.data = data

    @property
    def phone_number(self):
        return self.data.get("phone_number")

    def __getitem__(self, item):
        return self.data[item]

    def get(self, item, default=None):
        return self.data.get(item, default)

    def to_json(self):
        json_obj = self.data.copy()
        json_obj.pop("_id")
        return json_obj

    def get_hop_data(self):
        hop_id = self.get('hop_id')
        if hop_id is None:
            raise Exception("trying to get hop data for a user with no hop_id")
        return HopClient.get_customer(hop_id)

    def set(self, key, val):
        self.data[key] = val
        db.users.update_one({'psid': self.data['psid']}, {"$set": {key: val}})

    @classmethod
    def get_or_create_user(cls, psid):
        user_data = db.users.find_one({'psid': psid})
        if user_data is None:
            user_data = fb_get_user(psid)
            user_data['psid'] = str(psid)

            #hop_id = cls.__find_hop_best_match(User(user_data))
            #if hop_id is None:
            #    logger.error("exact match was not found for user {} so we are default to id 49".format(user_data))
            #    hop_id = 49
            #user_data['hop_id'] = int(hop_id)
            db.users.insert_one(user_data)
            logger.info("creating new user {}".format(user_data))
            user_data = db.users.find_one({'psid': psid})
        return cls.make_user_obj(user_data)

    @classmethod
    def __find_hop_best_match(cls, user):
        name = (user["first_name"] + " " + user["last_name"]).lower()
        customers = HopClient.get_customers()
        for cust in customers:
            if cust["full_name"].lower() == name:
                return cust["id"]

    @classmethod
    def find_by_hop_id(cls, hop_id):
        user_data = db.users.find_one({'hop_id': int(hop_id)})
        if user_data is None:
            logger.error("user with hop_id {} was not found".format(hop_id))
        return cls.make_user_obj(user_data)

    @classmethod
    def find_by_psid(cls, psid):
        user_data = db.users.find_one({'psid': psid})
        if user_data is None:
            logger.error("user with psid {} was not found".format(psid))
        return cls.make_user_obj(user_data)

    @classmethod
    def make_user_obj(cls, user_data):
        if user_data is not None:
            return User(user_data)
        return None


def is_valid_phone_number(s):
    """
    1) Begins with 0 or 91
    2) Then contains 7 or 8 or 9.
    3) Then contains 9 digits
    """
    return PHONE_PATTERN.match(s)


def post_to_fb(data):
    resp = requests.post(FB_ENDPOINT, json=data)
    logger.info("sending to fb: {}".format(data))
    db.messenger_log.insert_one({"data": data, "resp": resp.content})
    logger.info("fb response: {}".format(resp.content))


def send_buttons(psid, buttons, text="."):
    data = {
        "attachment": {
            "type": "template",
            "payload": {
                "text": text,
                "template_type": "button",
                "buttons": buttons
            }
        }
    }
    reply(psid, data)


def send_long_list(sender, elems):
    data = {
        "recipient": {
            "id": sender
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": '',
                    "elements": []
                }
            }
        }
    }

    data["message"]["attachment"]["payload"]["template_type"] = "list"
    data["message"]["attachment"]["payload"]["top_element_style"] = "compact"

    for i in range(0, len(elems), 3):
        sub_elems = elems[i:min(len(elems), i + 3)]
        data["message"]["attachment"]["payload"]["elements"] = sub_elems
        if len(sub_elems) == 1:
            sub_elems.append({"title": ".", "subtitle": "."})

        post_to_fb(data)


def reply_text(user_id, msg_txt):
    db.messenger_text.insert_one({"from": "hopscotch", "to": user_id, "msg": msg_txt})
    return reply(user_id, {"text": msg_txt})


def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": msg
    }
    post_to_fb(data)
    return 'ok'


def set_user_mode(user_id, mode):
    db.users.update({"psid": user_id}, {"$set": {"hops_mode": mode}})


def receive_question(user, msg):
    task_obj = {"name": "new_question",
                "payload": {"customer_id": user["hop_id"]}}
    return False

    try:
        res = requests.post(config["TASK_SERVER_URL"] + '/hooks/event', json=task_obj)
    except Exception as e:
        logger.error("failed to post to new question event {1} to the task server because {1}".format(
            task_obj, e
        ))
        return False
    if not res.ok:
        logger.error("failed to post to new question event {1} to the task server received error {1}".format(
            task_obj, res.content
        ))
        return False
    logger.info("received result from task server {}".format(res.json()))
    return bool(res.json().get("succ"))
