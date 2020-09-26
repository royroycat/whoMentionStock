from decimal import Decimal
from imapclient import IMAPClient
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import ssl
import email
from email.header import decode_header

db = None

def set_ark_helper(pony_db):
    global db
    db = pony_db

def grep_email(gmail_address, password):
        # Step 1. take latest date of ARK trading info, if no then take ytd date, take all emails
        target_date = db.ArkTradingInfo.get_latest_date() + timedelta(days=1)
        # To prevent ssl.SSLError
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        with IMAPClient(host="imap.gmail.com", ssl=True, ssl_context=context) as server:
            server.login(gmail_address, password)
            server.select_folder('INBOX', readonly=True)
            # Step 2. take the email title "ARK Investment Management Trading Information", if target_date is None, then set 3 days ago email
            if target_date is  None:
                target_date = datetime.now() - timedelta(days=3)
            messages = server.search(['SINCE', target_date, 'SUBJECT', 'ARK Investment Management Trading Information', 'FROM', 'ark@ark-funds.com'])
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
                        # ID | Fund | Date | Direction | Ticker | CUSIP | Company Shares | % of ETF
                        db.ArkTradingInfo(daily_id=int(d[0].get_text()),
                                        fund=d[1].get_text(),
                                        date=datetime.strptime(d[2].get_text(), '%m/%d/%Y'),
                                        direction=d[3].get_text(), 
                                        ticker=d[4].get_text(), 
                                        cusip=d[5].get_text(),
                                        company=d[6].get_text(),
                                        shares=Decimal(d[7].get_text().replace(",", "")),
                                        etf_percent=Decimal(d[8].get_text()),
                                        create_time=datetime.now())
                    rowIndex = rowIndex + 1

def get_matching_stock(ticker):
    return

def get_consecutive_trade(day=3):
    return