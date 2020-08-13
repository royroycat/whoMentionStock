from pony.orm import *
from datetime import datetime
from .base import db

class Tweet(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str)
    tweet = Optional(str)
    datetime = Optional(datetime)