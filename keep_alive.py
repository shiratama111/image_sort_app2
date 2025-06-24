"""
Webサーバーを起動してReplitのBotを稼働し続ける
UptimeRobotなどの外部監視サービスと組み合わせて使用
"""
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "AI えびすや Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()