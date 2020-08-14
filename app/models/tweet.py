from pony.orm import *
from datetime import datetime

def define_entity(db):
    class Tweet(db.Entity):
        id = PrimaryKey(int, auto=True)
        username = Required(str)
        tweet = Optional(str)
        datetime = Optional(datetime)