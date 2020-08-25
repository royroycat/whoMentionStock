from pony.orm import *
from datetime import datetime

def define_entity(db):
    class Tweet(db.Entity):
        _table_ = "tweet"
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        screen_name = Required(str)
        tweet_id = Required(int, size=64)
        tweet = Optional(unicode)
        url = Optional(unicode)
        mention_stock = Optional(str)
        datetime = Optional(datetime)