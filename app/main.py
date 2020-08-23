import json
from datetime import datetime
from flask import Flask, jsonify, request
from pony.flask import Pony
from pony.orm import *
from pony.orm.serialization import to_dict
import tweepy
from models import twitter_user as twitter_user_module
from models import stock as stock_module
from models import tweet as tweet_module

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

@app.route("/")
def index():
    # scheduler job to grep mention stock tweets
    # Step 1. loop all twitter_user
    # Step 2. get the last request id from specific user
    # Step 3. get all contents (after the last request id) from that twitter_user  
    # Step 4. scan the contents with stock ticker symbol and keywords
    # Step 5. if one is matched, save tweet in db, update stock time and send to tg
    user_list = db.TwitterUser.select()[:]
    stock_list = db.Stock.select()[:]
    for user in user_list:
        statuses = api.user_timeline(id=user.username, count=100, since_id=user.last_request_id)
        user.last_request_time = datetime.now()
        for status in statuses:
            if user.last_request_id is None:
                user.last_request_id = status.id
            if status.id > user.last_request_id:
                user.last_request_id = status.id
            for stock in stock_list:
                 for word in stock_module.get_words_list(stock):
                    if word in status.text:
                        with db_session:
                            db.Tweet(username=status.user.name, 
                                     tweet_id=status.id, 
                                     tweet=status.text, 
                                     mention_stock=stock.stock,
                                     datetime=datetime.now())
                            stock.last_request_id = status.id
                            stock.last_request_time = datetime.now()


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)