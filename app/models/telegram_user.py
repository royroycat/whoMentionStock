from pony.orm import *
from datetime import datetime

def define_entity(db):
    class TelegramUser(db.Entity):
        _table_ = "telegram_user"
        chat_id = PrimaryKey(int, size=64)
        update_id = Optional(int, size=64)
        first_name = Optional(str, nullable=True)
        last_name = Optional(str, nullable=True)
        username = Optional(str, nullable=True)
        type = Optional(str, nullable=True)
        title = Optional(str, nullable=True)
        all_are_admin = Optional(bool, nullable=True)
        create_time = Optional(datetime)
        can_receive_message = Required(bool, default=False)