import random
from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from fb_messenger_server.fb_app.utils import reply_text, User
from fb_messenger_server import db, logger

tool_app = Blueprint('tool_app', __name__)

LOGO_URL = "http://www.hopscotch.health/wp-content/uploads/2018/05/logo.png"


@tool_app.route("/tool/<int:hop_id>", methods=['GET'])
def messenger_tool(hop_id):
    user = User.find_by_hop_id(hop_id)
    if user is None:
        return jsonify({"err": "could not find user"})

    psid = user["psid"]
    if user is None:
        return jsonify({'success': False, 'message': 'user {} not found'.format(hop_id)}), 404
    messages = [{'from': v['from'], 'msg': v['msg']} for v in
                list(db.messenger_text.find({"$or": [{"to": psid}, {"from": psid}]}))]
    for msg in messages:
        if msg["from"] == psid:
            msg["name"] = user['first_name'] + ' ' + user['last_name']
            msg["img"] = user['profile_pic']
        elif msg["from"] == "hopscotch":
            msg["name"] = "hopscotch"
            msg["img"] = LOGO_URL

    return render_template(
        "messenger_tool.html",
        user=user,
        messages=messages[-min(len(messages), 10):]
    )


@tool_app.route("/tool/<int:hop_id>", methods=['POST'])
def messenger_tool_post(hop_id):
    user = User.find_by_hop_id(hop_id)
    if user is None:
        return jsonify({"err": "could not find user"})

    txt = request.form.get("reply")

    if txt:
        reply_text(user["psid"], txt)
    else:
        logger.warn("trying to send an empty reply")

    url = "{0}?v={1}".format(
        url_for('tool_app.messenger_tool', hop_id=hop_id),
        str(random.randint(0, 100000000)))
    return redirect(url)


@tool_app.route("/tool/", methods=['GET'])
def messenger_index():
    all_users = list(db.users.find({}))
    for u in all_users:
        u.pop('_id')
    return render_template(
        "messenger_index.html",
        users=all_users,
    )
