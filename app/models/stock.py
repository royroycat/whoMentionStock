from pony.orm import *
from datetime import datetime
from .base import db

class Stock(db.Entity):
    id = PrimaryKey(int, auto=True)
    stock = Required(str)
    keywords = Optional(str)
    last_request_id = Optional(int)
    last_request_time = Optional(datetime)