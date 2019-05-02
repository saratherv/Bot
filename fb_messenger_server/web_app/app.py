import json
from flask import Blueprint, request, render_template

web_app = Blueprint('web_app', __name__)


@web_app.route("/webview", methods=['GET'])
def webview_route():
    food_str = request.args.get("food_str")
    if food_str is None:
        foods = []
        print("no foods found")
    else:
        foods = json.loads(food_str)['foods']

    return render_template("food_webview.html", foods=foods)
