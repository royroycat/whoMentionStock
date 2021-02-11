import json
import schedule
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from pony.flask import Pony
from pony.orm import *
from pony.orm.serialization import to_dict
import tweepy   
from models import config as config_module
from models import twitter_user as twitter_user_module
from models import stock as stock_module
from models import tweet as tweet_module
from models import telegram_user as telegram_user_module
from models import ark_trading_info as ark_trading_info_module
from helpers import telegram_helper, ark_helper
from helpers.ta_helper import TAHelper
from threading import Thread
import traceback

app = Flask(__name__, instance_relative_config=True)
# for ./config.py
app.config.from_object('config')
# for instance/config.py, silent means missing file is ok
app.config.from_pyfile('config.py', silent=True) 

# Database
db = Database()
config_module.define_entity(db)
twitter_user_module.define_entity(db)
stock_module.define_entity(db)
tweet_module.define_entity(db)
telegram_user_module.define_entity(db)
ark_trading_info_module.define_entity(db)
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
tweepy_api = tweepy.API(auth)

# Pony
Pony(app)

# Flask-RESTful
restful_api = Api(app)
parser = reqparse.RequestParser()   
parser.add_argument('msg')
class Stock(Resource):
    def get(self):
        stock_list = db.Stock.select()[:]
        array = []
        for stock in stock_list:
            array.append(stock.stock.strip("$"))
        return jsonify(array)

class Telegram(Resource):
    def post(self):
        args = parser.parse_args()
        msg = args['msg']
        telegram_helper.send_message(msg)

restful_api.add_resource(Stock, '/stock')
restful_api.add_resource(Telegram, '/telegram')

# Main Function (Scheduler Task)
@db_session
def grep_mention_stock_tweets():
    try:
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
        combined_message = ''
        for user in user_list:
            # if twitter user is newcomer, grep 10 tweets is ok, or bomb the telegram
            if user.last_request_id is None: 
                statuses = tweepy_api.user_timeline(id=user.username, count=10, tweet_mode = 'extended')
            else: 
                statuses = tweepy_api.user_timeline(id=user.username, count=20, since_id=user.last_request_id, tweet_mode = 'extended')
            user.last_request_time = datetime.now()
            for status in statuses:
                if user.last_request_id is None:
                    user.last_request_id = status.id
                if status.id > user.last_request_id:
                    user.last_request_id = status.id
                for stock in stock_list:
                    for word in stock_module.get_words_list(stock):
                        if word.lower() in status.full_text.lower():
                            if db.Tweet.exists(lambda t: t.tweet_id == status.id) is True:
                                continue
                            print("Tweet inserted = " + str(status.id))
                            tweet_date_time = status.created_at.strftime("%m/%d/%Y, %H:%M:%S")
                            url = "https://twitter.com/%s/status/%s" % (status.user.screen_name, status.id)
                            # crop the output message to 280 per tweet length to prevent to long, and cannot display in telegram
                            combined_message += f"{status.user.name} : {tweet_date_time} : {url} : {status.full_text[:280] + ('..' if len(status.full_text) > 280 else '')} \n\n=====\n\n"
                            db.Tweet(name=status.user.name, 
                                    screen_name=status.user.screen_name,
                                    tweet_id=status.id, 
                                    tweet=status.full_text, 
                                    url= url,
                                    mention_stock=stock.stock,
                                    datetime=status.created_at)
                            stock.last_mention_id = status.id
                            stock.last_mention_time = datetime.now()
        if combined_message != '':
                telegram_helper.send_message(combined_message[:4090] + ('..' if len(combined_message) > 4090 else ''))    
    except Exception as e:
        traceback.print_exc()
        pass

def grep_ark_email():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(dt_string + " : grep_ark_email is running...")
    ark_helper.grep_email(app.config["GMAIL_ADDRESS"], app.config["GMAIL_PASSWORD"])
    combined_message = ''
    matching_stocks = ark_helper.get_matching_stock()
    for matching_stock in matching_stocks:
        combined_message += f"[ARK Alert] {matching_stock.ticker} : {matching_stock.direction} : {str(matching_stock.shares)} \n"
    if combined_message != '' :
        combined_message += '\n=============\n'

    consecutive_stock_dict = ark_helper.get_consecutive_trade()
    for key, value in consecutive_stock_dict.items():
        combined_message = combined_message + f"[ARK Action in consecutive] {key} ({value[0].company}) :\n"
        for info in value:
            date = info.date.strftime("%d/%m/%Y")
            combined_message += f"{date} {info.fund} {info.direction} {info.shares} {info.etf_percent}\n"
        combined_message += '\n=============\n'
    print("grep_ark_email log : " + combined_message)
    if combined_message != '':
        telegram_helper.send_message(combined_message[:4090] + ('..' if len(combined_message) > 4090 else ''))  

@db_session
def run_volume_compare_percentage_index():
    # get all stock ticker from API
    stock_list = db.Stock.select()[:]
    msg = '(LastDayVolume - 21AverageVolume) / 21AverageVolume) * 100\n==========\n'
    # create TAHelper for each ticker
    for stock in stock_list:
        ticker = stock.stock.strip("$")
        taHelper = TAHelper(ticker)
        index = taHelper.run_volume_compare_percentage_index()
        msg += '%s : %f%%\n' % (ticker, index)
    print(msg)
    telegram_helper.send_message(msg)
    pass

# ARK
ark_helper.set_ark_helper(pony_db=db)

# Schedule Job
schedule.every(20).minutes.do(grep_mention_stock_tweets)
schedule.every().day.at("01:15").do(grep_ark_email)
schedule.every().day.at("01:01").do(run_volume_compare_percentage_index)
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)  
t = Thread(target=run_schedule)
t.start()

# Telegram, once set_telegram_bot will block the thread
telegram_helper.set_telegram_bot(pony_db=db, token=app.config["TELEGRAM_TOKEN"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)