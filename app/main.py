from flask import Flask, jsonify
from pony.flask import Pony
from pony.orm import *
from pony.orm.serialization import to_dict
from models import twitter_user, stock, tweet
import json

app = Flask(__name__)
db = Database()
twitter_user.define_entity(db)
stock.define_entity(db)
tweet.define_entity(db)
db.bind(provider='mysql', 
        host='mysql', 
        user='whoMentionStock', 
        passwd='yourpassword', 
        db='whoMentionStock')
db.generate_mapping(create_tables=False)
Pony(app)

@app.route("/")
def index():
    userlist = db.TwitterUser.select()[:]
    result = []
    for p in userlist:
        result.append(p.to_dict())
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
    # scheduler job to grep mention stock tweets
    # Step 1. loop all twitter_user
    # Step 2. get all contents (after the last request id) from that twitter_user  
    # Step 3. scan the contents with stock ticker symbol and keywords
    # Step 4. if one is matched, save in db and send to tg