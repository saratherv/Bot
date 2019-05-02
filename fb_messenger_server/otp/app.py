import re
import pymongo
import time
from threading import Thread
from bson import ObjectId
from flask import Blueprint
import urllib.parse
import random
import datetime
from fb_messenger_server import logger, db
from fb_messenger_server.consts import API_KEY
from fb_messenger_server.fb_app.utils import User, is_valid_phone_number
from fb_messenger_server.hop_client import HopClient

otp = Blueprint('otp_app', __name__)


OTP_DURATION = 30 * 60
MAX_ATTEMPTS = 3


class OTPManager(object):
    otp_cache = {}

    @classmethod
    def get_otp_attempt(cls, psid, phone_number=None):
        oa = OTPManager.otp_cache.get(psid)
        if oa is None:
            latest_oa = list(db.otp_attempts.find({'user_psid': psid}).sort("start_time", pymongo.ASCENDING).limit(1))
            if len(latest_oa) > 0:
                oa = OTPAttempt.load_by_id(latest_oa[0]['_id'])
            else:
                oa = OTPAttempt(psid, phone_number=phone_number)
        OTPManager.otp_cache[oa] = oa
        return oa

    @classmethod
    def otp_failed(cls, otp_attempt):
        send_msg(otp_attempt.user_psid, "otp failed")


class OTPAttempt(object):
    def __init__(self, user_psid, phone_number=None, expecting_phone_number=False, otp_answer=None,
                 expecting_otp=False, start_time=None, n_attempts=0, success=False, _id=None, **kwargs):
        self.user_psid = user_psid
        self.phone_number = phone_number

        self.expecting_phone_number = expecting_phone_number
        self.otp_answer = otp_answer
        self.expecting_otp = expecting_otp
        self.start_time = start_time
        self.n_attempts = n_attempts
        self.success = success
        self._id = _id
        self.save()

        if self.is_active():
            t = Thread(target=self.timing_thread)
            t.daemon = True
            t.start()

    def timing_thread(self):
        while True:
            time.sleep(1)
            if not self.is_active():
                if not self.success:
                    OTPManager.otp_failed(self)
                break

    def is_active(self):
        if self.start_time is None:
            t_remaining = OTP_DURATION
        else:
            t_remaining = OTP_DURATION - (datetime.datetime.utcnow() - self.start_time).seconds
        return (not self.success) and (t_remaining > 0) and (self.n_attempts <= MAX_ATTEMPTS)

    @classmethod
    def load_by_id(cls, _id):
        obj = db.otp_attempts.find_one({'_id': ObjectId(_id)})
        return OTPAttempt(**obj)

    def to_json(self):
        obj = {
            'user_psid': self.user_psid,
            'expecting_phone_number': self.expecting_phone_number,
            'expecting_otp': self.expecting_otp,
            'n_attempts': self.n_attempts,
            'success': self.success,
            'active': self.is_active()
        }
        if self.otp_answer is not None:
            obj['otp_answer'] = self.otp_answer
        if self.phone_number is not None:
            obj['phone_number'] = self.phone_number
        if self.start_time is not None:
            obj['start_time'] = self.start_time
        if self._id is not None:
            obj['_id'] = self._id

        return obj

    def save(self):
        if self._id is None:
            res = db.otp_attempts.insert_one(self.to_json())
            self._id = res.inserted_id
        else:
            db.otp_attempts.replace_one({'_id': ObjectId(self._id)}, self.to_json())

    def next_step(self, msg=None):
        """
        :param str msg:
        :return:
        """
        if msg is not None:
            msg = msg.strip()
        if self.expecting_phone_number:
            if msg is None:
                reply = "we were not able to recognise that phone number, please try typing it again"
            else:
                phone = clean_phone_number(msg)
                if is_valid_phone_number(phone):
                    self.expecting_phone_number = False
                    self.send_otp_answer()
                    self.phone_number = phone
                    reply = "you will receive a 5 digit number on that phone. Please type that number here"
                else:
                    reply = "we were not able to recognise that phone number, please try typing it again"
        elif self.phone_number is None:
            reply = "please type in your phone number starting with the country code"
            self.expecting_phone_number = True
            self.expecting_otp = False
        elif self.expecting_otp:
            if msg == self.otp_answer:
                reply = "otp was successful"
                self.success = True
                self.expecting_otp = False
            else:
                t_remaining = OTP_DURATION - (datetime.datetime.utcnow() - self.start_time).seconds
                if t_remaining < 0:
                    reply = "sorry you have reached the maximum allowed time for the OTP, a customer representative will be with you shortly. Sorry about the inconvenience"
                elif self.n_attempts >= MAX_ATTEMPTS:
                    reply = "sorry you have reached the maximum OTP attempts, a customer representative will be with you shortly. Sorry about the inconvenience"
                else:
                    reply = "sorry your input is incorrect. {0} attempts and {1} minutes {2} seconds remaining".format(
                        MAX_ATTEMPTS - self.n_attempts, int(t_remaining / 60), int(t_remaining % 60))
                    self.n_attempts += 1
        elif self.is_active():
            self.send_otp_answer()
            reply = "you will receive a 5 digit number on that phone. Please type that number here"
        else:
            reply = "this OTP is no longer active"
        self.save()

        return reply

    def send_otp_answer(self):
        self.otp_answer = str(random.randint(10000, 99999))
        send_sms(self.phone_number, "Hopscotch Health OTP: {} please reply STOP if you did not request this OTP".format(self.otp_answer))
        self.expecting_otp = True
        self.start_time = datetime.datetime.utcnow()


def send_sms_for_real(number, content):
    data = urllib.parse.urlencode({'apikey': API_KEY, 'numbers': number,
                                   'message': content, 'sender': 'MYHOPS'})
    data = data.encode('utf-8')
    url = urllib.request.Request("https://api.textlocal.in/send/?")
    f = urllib.request.urlopen(url, data)
    fr = f.read()
    return fr


def send_sms(number, content):
    print(number, content)


def send_msg(psid, message):
    print('sending message to {0} "{1}"'.format(psid, message))


def run(v=None):
    user = User(db.users.find_one({"first_name": "Aaron"}))

    if user.get("hop_id") is None:
        oa = OTPManager.get_otp_attempt(user["psid"])
        if oa.is_active():
            msg = oa.next_step(v)
            if msg is not None:
                send_msg(user["psid"], msg)
        elif not oa.success:
            send_msg(user["psid"], "OTP is not active, a customer service specialist will be with you shortly.")
            logger.error("received message with no hop_id and no active OTP")

        if oa.success:
            matched_ids = find_hop_id_by_phone_number(oa.phone_number)
            if len(matched_ids) == 0:
                send_msg(user["psid"], "sorry we were not able to find your account")
                logger.error("no account matched")
            elif len(matched_ids) > 1:
                send_msg(user["psid"], "we have encountered an unexpected error while looking for your account")
                logger.error("multiple hop_ids for phone_number {}".format(oa.phone_number))
            else:
                send_msg(user["psid"], "thank you. Your account is now linked and active")
                user.set("phone_number", oa.phone_number)
                user.set("hop_id", matched_ids[0])
    else:
        send_msg(user["psid"], "normal stuff")


def clean_phone_number(phone_number):
    num = re.sub(r'[^0-9]', '', phone_number)
    return num[max(0, len(num) - 10):]


def find_hop_id_by_phone_number(phone_number):
    phone_number = clean_phone_number(phone_number)
    customers = HopClient.get_customers()
    for cust in customers:
        cust["phone_number_clean"] = clean_phone_number(cust["phone_number"])
    return [c["id"] for c in customers if c["phone_number_clean"] == phone_number]
