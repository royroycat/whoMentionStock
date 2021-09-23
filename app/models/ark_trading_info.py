from pony.orm import *
from decimal import Decimal
from datetime import datetime

def define_entity(db):
    class ArkTradingInfo(db.Entity):
        _table_ = "ark_trading_info"
        id = PrimaryKey(int, auto=True)
        daily_id=Required(int)
        fund = Required(str)
        date = Optional(datetime)
        direction = Required(str)
        ticker = Optional(str)
        region = Optional(str, nullable=True)
        cusip = Optional(str, nullable=True)
        company = Optional(str)
        shares = Required(Decimal)
        etf_percent = Required(Decimal)
        create_time = Required(datetime)

        @classmethod
        def get_latest_date(cls):
            return max(a.date for a in db.ArkTradingInfo)