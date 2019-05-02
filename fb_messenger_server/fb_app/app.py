import json
import urllib.parse
from flask import request, Blueprint

from fb_messenger_server.nutritionix import call_food_api, NXException
from fb_messenger_server.otp.app import OTPManager, find_hop_id_by_phone_number
from fb_messenger_server.consts import SERVER_URL
from fb_messenger_server.fb_app.utils import (reply_text, send_long_list, set_user_mode,
                                              handle_verification, User, reply,
                                              MEAL_MODE, QUESTION_MODE, receive_question, send_buttons)
from fb_messenger_server.fb_app.messages import PAYMENT_MESSAGE
from fb_messenger_server import logger, db

LOGO_URL = "http://www.hopscotch.health/wp-content/uploads/2018/05/logo.png"

fb_app = Blueprint('fb_app', __name__)

fb_app.add_url_rule('/auth', 'handle_verification', handle_verification, methods=['GET'])


@fb_app.route("/auth", methods=['POST'])
def handle_incoming_messages():
    """This function accepts all incoming requests"""
    data = request.json
    msg_obj = data['entry'][0]['messaging'][0]
    sender = msg_obj['sender']['id']
    user = User.get_or_create_user(sender)

    if 'message' in msg_obj:
        if user.get("hop_id") is None:
            return handle_otp(user, msg_obj["message"]["text"])
        else:
            return handle_message(user, msg_obj["message"]["text"])
    elif 'postback' in msg_obj:
        if user.get("hop_id") is None:
            return handle_otp(user, None)
        else:
            return handle_postback(user, msg_obj["postback"]["payload"])
    else:
        return "ok"


def handle_otp(user, message=None):
    oa = OTPManager.get_otp_attempt(user["psid"])
    if oa.is_active():
        msg = oa.next_step(message)
        if msg is not None:
            reply_text(user["psid"], msg)
    elif not oa.success:
        reply_text(user["psid"], "OTP is not active, a customer service specialist will be with you shortly.")
        logger.error("received message with no hop_id and no active OTP")

    if oa.success:
        matched_ids = find_hop_id_by_phone_number(oa.phone_number)
        if len(matched_ids) == 0:
            reply_text(user["psid"], "sorry we were not able to find your account")
            logger.error("no account matched")
        elif len(matched_ids) > 1:
            reply_text(user["psid"], "we have encountered an unexpected error while looking for your account")
            logger.error("multiple hop_ids for phone_number {}".format(oa.phone_number))
        else:
            reply_text(user["psid"], "thank you. Your account is now linked and active")
            user.set("phone_number", oa.phone_number)
            user.set("hop_id", matched_ids[0])


def handle_message(user, message):
    db.messenger_text.insert_one({"from": user["psid"], "to": "hopscotch", "msg": message})
    mode = user.get('hops_mode', 'default')
    if mode == MEAL_MODE:
        try:
            resp = call_food_api(message)
        except NXException:
            logger.warn("could not find nx food for '{}'".format(message))
            resp = {}
        try:
            foods = resp["foods"]
        except KeyError:
            logger.warn("nx sent back response with out 'foods' key")
            foods = []

        if len(foods) > 0:
            send_food_data(user['psid'], foods)
        else:
            reply_text(user['psid'], "Sorry we didn't understand that. Please type in the meal you had like this: '1 egg and 2 chaptis'")
        set_user_mode(user['psid'], 'default')
    elif mode == QUESTION_MODE:
        if receive_question(user, message):
            reply_text(user['psid'], "Your question has been sent to a nutritionist and you will receive a response within 24 business hours")
        else:
            reply_text(user['psid'], "Sorry we were unable to send your question. Our team has been alerted about this error. Thank you for your patience")
        set_user_mode(user['psid'], 'default')
    else:
        if mode != 'default':
            logger.error("user has unexpected mode '{}'".format(mode))
            return 'ok'
        send_buttons(user['psid'], [
            {
                "type": "postback",
                "title": "Log a Meal",
                "payload": "meal"
            },
            {
                "type": "postback",
                "title": "Ask a Question",
                "payload": "question"
            },
        ], "Sorry we didn't understand that. Please select from these choices")
    return 'ok'


def handle_postback(user, message):
    if message == "Let's get started":
        reply(user['psid'], PAYMENT_MESSAGE)
    elif message == 'meal':
        reply_text(user['psid'], "Please enter food in this format '1 egg and 1 apple'")
        set_user_mode(user['psid'], MEAL_MODE)
    elif message == 'question':
        reply_text(user['psid'], "Please write your question here and our nutritionist will reply in 24 hours")
        set_user_mode(user['psid'], QUESTION_MODE)
    else:
        logger.warn("received unknown postback {}".format(message))
    return "ok"


def send_food_data(psid, foods):
    db.food_log.insert_one({"user": psid, "foods": foods})

    # add header
    elems = [
        {
            "title": "Here is your meal",
            "image_url": LOGO_URL
        }
    ]

    # add foods
    for food in foods:
        t = "Calorie:{nf_calories} Carbohydrate:{nf_total_carbohydrate} Fat:{nf_total_fat} Protein:{nf_protein}".format(
            **food)
        elems.append({
            "title": "{food_name}: {serving_qty} {serving_unit}".format(**food),
            "subtitle": t,
            "image_url": food['photo']['highres']
        })

    # add webview
    wv_foods = []
    for food in foods:
        t = "Calorie:{nf_calories} Carbohydrate:{nf_total_carbohydrate} Fat:{nf_total_fat} Protein:{nf_protein}".format(
            **food)
        wv_foods.append({
            "name": "{food_name}: {serving_qty} {serving_unit}".format(**food),
            "detail": t,
            "img": food['photo']['highres']
        })
    query_str = urllib.parse.urlencode({'food_str': json.dumps({"foods": wv_foods})})

    send_long_list(psid, elems)
    send_buttons(psid, [{
        "type": "web_url",
        "url": SERVER_URL + "/webview?" + query_str,
        "title": "go to webview",
        "webview_height_ratio": "tall",
    }])
    return 'ok'
