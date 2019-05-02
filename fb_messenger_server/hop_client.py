from fb_messenger_server import config
import requests
from requests.exceptions import ConnectionError


NUTRITION_APP_URL = config["NUTRITION_SERVER_URL"]


class HopClient(object):

    @classmethod
    def put_customer(cls, customer):
        assert "id" in customer
        try:
            obj = requests.put(NUTRITION_APP_URL + "/api/users/{}".format(customer["id"]), json=customer)
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if not obj.ok:
            raise Exception("failed to get success response because " + str(obj.content))

        return obj.json()

    @classmethod
    def get_customers(cls):
        try:
            obj = requests.get(NUTRITION_APP_URL + "/api/users")
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if not obj.ok:
            raise Exception("failed to get success response because " + str(obj.content))

        return obj.json()["users"]

    @classmethod
    def get_customer(cls, cust_id):
        try:
            obj = requests.get(NUTRITION_APP_URL + "/api/users/{}".format(cust_id))
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if not obj.ok:
            raise Exception("failed to get success response because " + str(obj.content))

        try:
            return obj.json()["user"]
        except KeyError:
            raise Exception("could not find customer with id " + str(cust_id))

    @classmethod
    def get_payments(cls, cust_id):
        try:
            obj = requests.get(NUTRITION_APP_URL + "/api/users/{}/payments".format(cust_id))
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if not obj.ok:
            raise Exception("failed to get success response because " + str(obj.content))

        try:
            return obj.json()["payments"]
        except KeyError:
            raise Exception("could not find customer with id " + str(cust_id))

    @classmethod
    def post_payment(cls, payment, cust_id=None):
        if cust_id:
            payment["user_id"] = cust_id
        try:
            res = requests.post(NUTRITION_APP_URL + "/api/users/{}/payments".format(payment["user_id"]),
                                json=payment)
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if res.ok:
            return res.json()
        raise Exception("problem with response: " + str(res.content))

    @classmethod
    def update_payment(cls, payment, cust_id=None, payment_id=None):
        if cust_id:
            payment["user_id"] = cust_id
        if payment_id:
            payment["id"] = payment_id

        try:
            url = NUTRITION_APP_URL + "/api/users/{0}/payments/{1}".format(payment["user_id"], payment["id"])
            res = requests.put(url, json=payment)
        except ConnectionError as e:
            raise Exception("could not complete hopclient request because " + str(e))

        if res.ok:
            return res.json()
        raise Exception("problem with response: " + str(res.content))
