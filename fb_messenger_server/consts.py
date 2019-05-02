from fb_messenger_server import config
from .secrets import ACCESS_TOKEN
VERIFY_TOKEN = config["VERIFY_TOKEN"]
FB_ENDPOINT = "https://graph.facebook.com/v2.6/me/messages?access_token={}".format(ACCESS_TOKEN)
SERVER_URL = config["SERVER_URL"]
API_KEY = config["API_KEY"]
