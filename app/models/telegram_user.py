from pony.orm import *
from datetime import datetime

def define_entity(db):
    class TelegramUser(db.Entity):
        _table_ = "telegram_user"
        chat_id = PrimaryKey(int, size=64)
        first_name = Required(str)
        last_name = Required(str)
        username = Optional(str)
        create_time = Optional(datetime)