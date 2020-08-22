from pony.orm import *
from datetime import datetime

def define_entity(db):
    class TwitterUser(db.Entity):
        _table_ = "twitter_user"
        id = PrimaryKey(int, auto=True)
        username = Required(str)
        last_request_id = Optional(int, size=64)
        last_request_time = Optional(datetime)