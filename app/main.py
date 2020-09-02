import json
import schedule
import time
from datetime import datetime
from flask import Flask, jsonify, request
from pony.flask import Pony
from pony.orm import *
from pony.orm.serialization import to_dict
import tweepy   
from models import twitter_user as twitter_user_module
from models import stock as stock_module
from models import tweet as tweet_module
from models import telegram_user as telegram_user_module
from helpers import telegram_helper
import threading

app = Flask(__name__, instance_relative_config=True)
# for ./config.py
app.config.from_object('config')
# for instance/config.py, silent means missing file is ok
app.config.from_pyfile('config.py', silent=True) 

# Database
db = Database()
twitter_user_module.define_entity(db)
stock_module.define_entity(db)
tweet_module.define_entity(db)
telegram_user_module.define_entity(db)
db.bind(provider='mysql', 
        host=app.config["DB_HOST_NAME"],
        user=app.config["DB_USER"], 
        passwd=app.config["DB_PASSWORD"], 
        db=app.config["DB_DATABASE"],
        charset='utf8mb4')
db.generate_mapping(create_tables=False)

# Tweepy
auth = tweepy.OAuthHandler(app.config["TWITTER_CONSUMER_KEY"], app.config["TWITTER_CONSUMER_SECRET"])
auth.set_access_token(app.config["TWITTER_ACCESS_TOKEN"], app.config["TWITTER_ACCESS_TOKEN_SECRET"])
api = tweepy.API(auth)

# Pony
Pony(app)

@db_session
def grep_mention_stock_tweets():
    # scheduler job to grep mention stock tweets
    # Step 1. loop all twitter_user
    # Step 2. get the last request id from specific user
    # Step 3. get all contents (after the last request id) from that twitter_user  
    # Step 4. scan the contents with stock ticker symbol and keywords
    # Step 5. if one is matched, save tweet in db, update stock time and send to tg
    
    # some printout for log
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(dt_string + " : grep_mention_stock_tweets is running...")

    user_list = db.TwitterUser.select()[:]
    stock_list = db.Stock.select()[:]
    for user in user_list:
        # if twitter user is newcomer, grep 10 tweets is ok, or bomb the telegram
        if user.last_request_id is None: 
            statuses = api.user_timeline(id=user.username, count=10)
        else: 
            statuses = api.user_timeline(id=user.username, count=100, since_id=user.last_request_id)
        user.last_request_time = datetime.now()
        for status in statuses:
            if user.last_request_id is None:
                user.last_request_id = status.id
            if status.id > user.last_request_id:
                user.last_request_id = status.id
            for stock in stock_list:
                 for word in stock_module.get_words_list(stock):
                    if word.lower() in status.text.lower():
                        tweet_date_time = status.created_at.strftime("%m/%d/%Y, %H:%M:%S")
                        url = "https://twitter.com/%s/status/%s" % (status.user.screen_name, status.id)
                        telegram_helper.send_message(status.user.name + " : " + 
                                                     tweet_date_time + " : " + 
                                                     url + " : " + 
                                                     status.text)
                        db.Tweet(name=status.user.name, 
                                 screen_name=status.user.screen_name,
                                 tweet_id=status.id, 
                                 tweet=status.text, 
                                 url= url,
                                 mention_stock=stock.stock,
                                 datetime=status.created_at)
                        stock.last_mention_id = status.id
                        stock.last_mention_time = datetime.now()
                        continue

# Schedule Job
schedule.every(10).minutes.do(grep_mention_stock_tweets)
class ScheduleThread(threading.Thread):
    def __init__(self, *pargs, **kwargs):
        super().__init__(*pargs, daemon=True, name="scheduler", **kwargs)

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(schedule.idle_seconds())

ScheduleThread().start()

# Telegram
telegram_helper.set_telegram_bot(pony_db=db, token=app.config["TELEGRAM_TOKEN"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)