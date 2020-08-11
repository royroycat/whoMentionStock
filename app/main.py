from flask import Flask
from pony.flask import Pony
app = Flask(__name__)
db = Database()
db.bind(provider='mysql', host='127.0.0.1', user='whoMentionStock', passwd='yourpassword', db='whoMentionStock')
Pony(app)

@app.route("/")
def index():
    return "Welcome to whoMentionStock"   

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
    # scheduler job to grep mention stock tweets
    # Step 1. loop all twitter_user
    # Step 2. get all contents (after the last request id) from that twitter_user  
    # Step 3. scan the contents with stock ticker symbol and keywords
    # Step 4. if one is matched, save in db and send to tg