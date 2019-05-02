from flask import Flask
from fb_messenger_server.fb_app import fb_app
from fb_messenger_server.web_app import web_app
from fb_messenger_server.tool import tool_app
from fb_messenger_server.add_button_script import add_all_buttons

app = Flask(__name__)
app.secret_key = "secret"

app.register_blueprint(web_app)
app.register_blueprint(fb_app)
app.register_blueprint(tool_app)

add_all_buttons()


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == "__main__":
    app.run(debug=True, port=5000)