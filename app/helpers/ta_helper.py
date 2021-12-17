import yfinance as yf
from ta.volume import OnBalanceVolumeIndicator

class TAHelper:
    
    def __init__(self, ticker):
        self.ticker = ticker
        self.yfObject = yf.Ticker(self.ticker)
        
    # 1. Take average of this 21days volume
    # 2. Cal today OBV using with the previous 21days data
    # 3. todayObv / average21Vol
    # If index is + and huge mean big volume buying and up
    # If index is - and huge mean big volume selling and down 
    def run_volume_compare_percentage_index(self):
        percentChange = (self.yfObject.info['currentPrice'] - self.yfObject.info['previousClose']) / self.yfObject.info['previousClose'] * 100
        percentChange = round(percentChange, 2)
        hist = self.yfObject.history(period="22d")
        average21Vol = hist['Volume'][:-1].mean()
        todayVol = hist['Volume'].tail(1)
        index = ((todayVol - average21Vol) / average21Vol) * 100
        return index, percentChange

    def get_earnings_calendar(self):
        calendar = self.yfObject.calendar
        # calendars has 1 item means the earnings date is confirm 
        # while 2 item means not yet confirm but only a date range
        if calendar is None or len(calendar.columns) == 0:
            return None
        print(self.ticker)
        print(calendar.info)
        print(len(calendar.columns))
        if len(calendar.columns) >= 1:
            # the alert should be the 2/1/today days before the earnings date
            return calendar