from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route("/") #127.0.0.1
def index():
    return send_from_directory("html", "index.html") #127.0.0.1/html/css/b.css

@app.route('/<path:name>') #127.0.0.1/css/b.css
def start(name):
    return send_from_directory("html", name) #127.0.0.1/html/css/b.css