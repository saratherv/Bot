from fb_messenger_server.server import app

if __name__ == "__main__":
    app.run('0.0.0.0', debug=True, port=5000)
