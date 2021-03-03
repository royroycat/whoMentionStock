from decimal import Decimal
from imapclient import IMAPClient
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import ssl
import email
from email.header import decode_header
from collections import Counter
from itertools import dropwhile
from pony.orm import *
import csv
import requests
import os


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
            # Step 2. take the email title "ARK Investment Management LLC – Actively Managed ETFs - Daily Trade Information*", if email_date is None, then set 3 days ago email
            messages = server.search(['SINCE', email_date, 'SUBJECT', u'ARK Investment Management LLC Actively Managed ETFs', 'FROM', 'ark@ark-funds.com'])
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
                            # ID | Fund | Date | Direction | Ticker(.Region) | CUSIP | Company Shares | % of ETF
                            db.ArkTradingInfo(daily_id=int(d[0].get_text()),
                                            fund=d[1].get_text(),
                                            date=buyDate,
                                            direction=d[3].get_text(), 
                                            ticker=d[4].get_text().split(".")[0],
                                            region=d[4].get_text().split(".")[1] if len(d[4].get_text().split(".")) > 1 else None,
                                            cusip=d[5].get_text(),
                                            company=d[6].get_text(),
                                            shares=Decimal(d[7].get_text().replace(",", "")),
                                            etf_percent=Decimal(d[8].get_text()),
                                            create_time=datetime.now())
                    rowIndex = rowIndex + 1

@db_session
def get_matching_stock():
    stocks = db.Stock.select()[:]
    stock_names = []
    for s in stocks:
        stock_names.append(s.stock.strip("$"))
    trading_infos = db.ArkTradingInfo.select(lambda a:a.ticker in stock_names and (a.date == datetime.now().date() or a.date == datetime.now().date()- timedelta(days=1)))[:]
    return trading_infos

@db_session
def get_consecutive_trade(day=3):
    trading_infos = db.ArkTradingInfo.select_by_sql("select t1.* from ark_trading_info t1 inner join (SELECT distinct date FROM ark_trading_info WHERE date <= NOW() ORDER BY date desc limit $day) as t2 on t2.date = t1.date")
    ticker_dict = {}
    for i in trading_infos:
        if i.ticker not in ticker_dict.keys():
            ticker_dict[i.ticker] = []
        ticker_dict[i.ticker].append(i)
    specific_ticker_dict = {k:v for k,v in ticker_dict.items() if len(v) >= day}
    return specific_ticker_dict

@db_session
def get_ticker_history(ticker):
    trading_infos = db.ArkTradingInfo.select(lambda a:a.ticker==ticker and a.date >= datetime.now().date() - timedelta(days=60))
    return trading_infos

@db_session
def get_trading_info_by_date(date):
    trading_infos = db.ArkTradingInfo.select(lambda a:a.date == date.date())
    return trading_infos

@db_session
def grep_ark_daily_fund_holding(ark_ticker, ark_url):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(dt_string + " : grep_ark_daily_fund_holding is running...")
    print(f"grep {ark_ticker} with {ark_url}")
    csv_folder_path = "/root/whoMentionStock/ark_fund_csv"

    # 1. download the csv in mounted volume
    # 2. read the csv per fund
    # 3. if csv date > latest record date, so it is new csv
    # 4. save each record to sql

    r = requests.get(ark_url, allow_redirects=True)
    decoded_content = r.content.decode('utf-8')
    csv_reader = csv.reader(decoded_content.splitlines(), delimiter=',')
    holding_list = list(csv_reader)
    csv_date_string = holding_list[1][0]
    csv_datetime_obj = datetime.strptime(csv_date_string, '%m/%d/%Y')

    fund_latest_date = db.ArkFundHolding.get_latest_date(ark_ticker)
    
    if fund_latest_date is None or csv_datetime_obj.date() > fund_latest_date.date() :
        # save the record to db
        for index, holding in enumerate(holding_list):
            if (index==0):
                continue
            # when record is empty then stop
            if (not holding[0]):
                break
            holding_date = datetime.strptime(holding[0], '%m/%d/%Y')
            db.ArkFundHolding(daily_id=index,
                              date=holding_date,
                              fund=holding[1],
                              company=holding[2],
                              ticker=holding[3],
                              cusip=holding[4],
                              shares=holding[5],
                              market_value=holding[6],
                              weight=holding[7],
                              create_time=datetime.now())
        # backup the csv
        # for folder name
        csv_year_month_string = csv_datetime_obj.strftime("%Y%m")
        # for csv file name
        csv_year_month_day_string = csv_datetime_obj.strftime("%Y%m%d")
        last_slash_position = ark_url.rfind("/")
        csv_name = ark_url[last_slash_position+1:len(ark_url)]
        csv_name_without_extension = csv_name.split('.')[0]
        csv_file_path = f"{csv_folder_path}/{csv_year_month_string}/{csv_name_without_extension}_{csv_year_month_day_string}.csv"
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        open(csv_file_path, "wb").write(r.content)