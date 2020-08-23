from pony.orm import *
from datetime import datetime

def define_entity(db):
    class Stock(db.Entity):
        _table_ = "stock"
        id = PrimaryKey(int, auto=True)
        stock = Required(str)
        keywords = Optional(str)
        last_mention_id = Optional(int, size=64)
        last_mention_time = Optional(datetime)

def get_words_list(stock):
    name = stock.stock
    if stock.keywords is not None:
        keywords = [x.strip() for x in stock.keywords.split(',')]
        keywords.insert(0, name)
        return keywords
    else: 
        return [name]