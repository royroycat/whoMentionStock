from decimal import Decimal
from imapclient import IMAPClient
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import ssl
import email
from email.header import decode_header
from collections import Counter
from itertools import dropwhile

db = None

def set_ark_helper(pony_db):
    global db
    db = pony_db

@db_session
def grep_email(gmail_address, password):
        # Step 1. take latest date of ARK trading info, if no then take ytd date, take all emails
        latest_date = db.ArkTradingInfo.get_latest_date()
        email_date = None
        if latest_date is None:
            email_date = datetime.now() - timedelta(days=3)
        else:
            email_date = latest_date + timedelta(days=1)
        # To prevent ssl.SSLError
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        with IMAPClient(host="imap.gmail.com", ssl=True, ssl_context=context) as server:
            server.login(gmail_address, password)
            server.select_folder('INBOX', readonly=True)
            # Step 2. take the email title "ARK Investment Management Trading Information", if email_date is None, then set 3 days ago email
            messages = server.search(['SINCE', email_date, 'SUBJECT', 'ARK Investment Management Trading Information', 'FROM', 'ark@ark-funds.com'])
            for uid, message_data in server.fetch(messages, 'RFC822').items():
                email_message = email.message_from_bytes(message_data[b'RFC822'])
                content = email_message.get_payload(None, True)
                soup = BeautifulSoup(content, 'html.parser')
                # Step 3. Parse the table format into ArkTradingInfo entity
                table = soup.find(lambda tag: tag.name=='table') 
                rows = table.findAll(lambda tag: tag.name=='tr')
                rowIndex = 0
                for r in rows:
                    if rowIndex >= 1:
                        # grep and pass to db
                        d = r.findAll(lambda tag: tag.name=='td')
                        buyDate =  datetime.strptime(d[2].get_text(), '%m/%d/%Y')
                        # To prevent same data duplicate insert, use buyDate to do validation
                        if buyDate.date() > latest_date.date() or latest_date is None:
                            # ID | Fund | Date | Direction | Ticker | CUSIP | Company Shares | % of ETF
                            db.ArkTradingInfo(daily_id=int(d[0].get_text()),
                                            fund=d[1].get_text(),
                                            date=buyDate,
                                            direction=d[3].get_text(), 
                                            ticker=d[4].get_text(), 
                                            cusip=d[5].get_text(),
                                            company=d[6].get_text(),
                                            shares=Decimal(d[7].get_text().replace(",", "")),
                                            etf_percent=Decimal(d[8].get_text()),
                                            create_time=datetime.now())
                    rowIndex = rowIndex + 1

def get_matching_stock():
    stocks = db.Stock.select()[:]
    stock_names = []
    for s in stocks:
        stock_names.append(s.stock.strip("$"))
    trading_infos = db.ArkTradingInfo.select(lambda a:a.ticker in stock_names and a.date == datetime.now().date())[:]
    return trading_infos

def get_consecutive_trade(day=3):
    trading_infos = db.ArkTradingInfo.select_by_sql("select t1.* from ark_trading_info t1 inner join (SELECT distinct date FROM ark_trading_info WHERE date <= NOW() ORDER BY date desc limit $day) as t2 on t2.date = t1.date")
    ticker_dict = {}
    for i in trading_infos:
        if i.ticker not in ticker_dict.keys():
            ticker_dict[i.ticker] = []
        ticker_dict[i.ticker].append(i)
    specific_ticker_dict = {k:v for k,v in ticker_dict.items() if len(v) >= day}
    return specific_ticker_dict

def get_ticker_history(ticker):
    trading_infos = db.ArkTradingInfo.select(lambda a:a.ticker==ticker and a.date >= datetime.now().date() - timedelta(days=60))
    return trading_infos