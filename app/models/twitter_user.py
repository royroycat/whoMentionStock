from pony.orm import *
from datetime import datetime
from .base import db

class TwitterUser(db.Entity):
    _table_ = "twitter_user"
    id = PrimaryKey(int, auto=True)
    username = Required(str)
    last_request_time = Optional(datetime)