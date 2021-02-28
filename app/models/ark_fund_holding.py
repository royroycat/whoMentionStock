from pony.orm import *
from decimal import Decimal
from datetime import datetime

def define_entity(db):
    class ArkFundHolding(db.Entity):
        _table_ = "ark_fund_holding"
        id = PrimaryKey(int, auto=True)
        daily_id=Required(int)
        date = Optional(datetime)
        fund = Required(str)
        company = Optional(str)
        ticker = Optional(str)
        cusip = Optional(str)
        shares = Required(Decimal)
        market_value = Required(Decimal)
        weight = Required(Decimal)
        create_time = Required(datetime)

        @classmethod
        def get_latest_date(cls, ark_ticker):
            return max(a.date for a in db.ArkFundHolding if a.fund==ark_ticker)