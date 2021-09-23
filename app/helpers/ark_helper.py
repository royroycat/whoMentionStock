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
        # Step 1. take latest date of ARK trading info, if no then take 3 days before, take all emails / if halt too long ago (>1 days), take 3 days before too
        global latest_date
        global all_row_index
        latest_date = db.ArkTradingInfo.get_latest_date()
        email_date = datetime.now() - timedelta(days=3)

        # To prevent ssl.SSLError
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        with IMAPClient(host="imap.gmail.com", ssl=True, ssl_context=context) as server:
            server.login(gmail_address, password)
            server.select_folder('INBOX', readonly=True)
            # Step 2. take the email title "ARK Investment Management LLC – Actively Managed ETFs - Daily Trade Information*", if email_date is None, then set 3 days ago email
            messages = server.search(['SINCE', email_date, 'SUBJECT', u'ARK Investment Management LLC Actively Managed ETFs', 'FROM', 'ark@ark-funds.com'])
            for uid, message_data in server.fetch(messages, 'RFC822').items():
                all_row_index = 0
                email_message = email.message_from_bytes(message_data[b'RFC822'])
                content = email_message.get_payload(None, True)
                soup = BeautifulSoup(content, 'html.parser')
                # Step 3. Parse the table format into ArkTradingInfo entity
                grep_fund_info_from_email(soup, "ARKK ")
                grep_fund_info_from_email(soup, "ARKQ ")
                grep_fund_info_from_email(soup, "ARKW ")
                grep_fund_info_from_email(soup, "ARKG ")
                grep_fund_info_from_email(soup, "ARKF ")
                grep_fund_info_from_email(soup, "ARKX ")

@db_session
def grep_fund_info_from_email(soup, fund_name):
    global all_row_index
    # find the fund table which contains data with row
    tds= soup.find_all("td")
    td = None
    for this_td in tds:
        if fund_name in this_td.contents[0]:
            td = this_td
            break
    if td is None: # Catherine Wood has not trade on this fund today...
        return
    date_td = td.findNextSibling("td")
    buy_date = datetime.strptime(date_td.getText(), '%m/%d/%Y')
    fund_title_table = td.findParent("table")
    fund_table = fund_title_table.findNextSibling("table")
    rows = fund_table.findAll(lambda tag: tag.name=='tr')
    row_per_fund_index = 0
    for r in rows:
        # row_per_fund_index == 1 is title header
        if row_per_fund_index >= 1:
            # grep and pass to db
            d = r.findAll(lambda tag: tag.name=='td')
            # To prevent same data duplicate insert, use buyDate to do validation
            if latest_date is None or buy_date.date() > latest_date.date():
                all_row_index = all_row_index + 1
                # Direction | Ticker | Company Name | Shares Traded | % of Total ETF
                db.ArkTradingInfo(daily_id=all_row_index,
                                    fund=fund_name,
                                    date=buy_date,
                                    direction=d[0].getText(), 
                                    ticker=d[1].getText(),
                                    region=None,
                                    cusip=None,
                                    company=d[2].getText(),
                                    shares=Decimal(d[3].getText().strip().split('|')[0].replace(",", "")),
                                    etf_percent=Decimal(d[3].getText().strip().split('|')[1]),
                                    create_time=datetime.now())
        row_per_fund_index = row_per_fund_index + 1

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

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.get(ark_url, allow_redirects=True, headers=headers)
    
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