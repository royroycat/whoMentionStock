from pony.orm import *
from datetime import datetime

def define_entity(db):
    class Tweet(db.Entity):
        id = PrimaryKey(int, auto=True)
        username = Required(str)
        tweet_id = Required(int, size=64)
        tweet = Optional(str)
        mention_stock = Optional(str)
        datetime = Optional(datetime)