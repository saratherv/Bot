import json
import requests

# KEEP THIS FILE VERY PRIVATE BECAUSE IT CONTAINS THE API KEY
APP_ID = "enter app id"
APP_KEY = "enter you key"


class NXException(BaseException):
    pass


class NXClient(object):
    SEARCH_END_POINT = "https://trackapi.nutritionix.com/v2/search/instant"
    FOOD_END_POINT = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    HEADERS = {"Content-Type": "application/json",
               "x-app-id": APP_ID, "x-app-key": APP_KEY}

    @classmethod
    def search(cls, txt):
        v = requests.get(cls.SEARCH_END_POINT, params={"query": txt}, headers=cls.HEADERS)
        if v.status_code != 200:
            raise NXException("could not use nutritionix API")
        return json.loads(v.content.decode('utf-8'))

    @classmethod
    def food(cls, txt):
        body = json.dumps({"query": txt})
        v = requests.post(cls.FOOD_END_POINT, data=body, headers=cls.HEADERS)
        if v.status_code != 200:
            raise NXException("could not use nutritionix API")
        return json.loads(v.content.decode('utf-8'))


def call_food_api(food_name):
    """
    :param str food_name: food name or sentence
    :rtype Dict:
    """
    return NXClient.food(food_name)
