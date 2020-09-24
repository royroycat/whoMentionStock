from imapclient import IMAPClient
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
        target_date = db.ArkTradingInfo.get_latest_date()
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
                print(uid, email_message.get('From'), email_message.get('Subject'), email_message.get_payload(None, True))
                # Step 3. Parse the table format into ArkTradingInfo entity
                # Step 4. save it and update target date to config


def get_matching_stock(ticker):
    # If ticker 
    return

def get_consecutive_trade(day=3):
    return