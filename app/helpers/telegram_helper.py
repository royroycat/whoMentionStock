import requests
import traceback
from telegram.ext import Updater
from telegram.ext import CommandHandler
from datetime import datetime, date, timedelta
from pony.orm import *
import telegram
from helpers import ark_helper
from helpers.ta_helper import TAHelper

updater = None
dispatcher = None
db = None

@db_session
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to whoMentionBot")
    # save down the chat id afterwards
    user = db.TelegramUser(chat_id=update.effective_chat.id, 
                           update_id=update.update_id,
                           first_name=update.effective_chat.first_name or None,
                           last_name=update.effective_chat.last_name or None,
                           username=update.effective_chat.username or None,
                           type=update.effective_chat.type or None,
                           title=update.effective_chat.title or None,
                           all_are_admin=update.effective_chat.all_members_are_administrators or None,
                           create_time=datetime.now())
    if update.effective_chat.username is not None:
        user.username = update.effective_chat.username

@db_session
def command_ticker_history_handler(update, context):
    try:
        ticker = context.args[0]
    except IndexError:
        ticker = "TSLA"
    print("[Command Ticker History Handler] User asked for = " + ticker)
    trading_infos = ark_helper.get_ticker_history(ticker)
    if trading_infos:
        company = list(trading_infos)[0].company.replace('\n', ' ')
        combined_message = f"{ticker} ({company}) :\n"
        for info in trading_infos:
            date = info.date.strftime("%d/%m/%Y")
            combined_message += f"{date} {info.fund} {info.direction} {info.shares} {info.etf_percent}\n"
        print("command_ark_history_handler log = " + combined_message)
        update.message.reply_text(combined_message)

@db_session
def command_date_history_handler(update, context):
    try:
        date_string = context.args[0]
        input_date = datetime.strptime(date_string, '%d/%m/%Y')
    except IndexError: #if no input then set ytd
        latest_date = db.ArkTradingInfo.get_latest_date()
        date_string = latest_date.strftime("%d/%m/%Y")
        input_date = datetime.strptime(date_string, '%d/%m/%Y')
        
    print("[Command Date History Handler] User asked for = " + date_string)
    trading_infos = ark_helper.get_trading_info_by_date(input_date)
    if trading_infos:
        combined_message = f"{date_string} :\n"
        for info in trading_infos:
            combined_message += f"{info.fund} {info.ticker} {info.direction} {info.shares} {info.etf_percent}\n"
        print("command_date_history_handler log = " + combined_message)
        update.message.reply_text(combined_message)

@db_session
def command_volume_compare_handler(update, context):
    ticker_list = []
    try:
        ticker_list.append(context.args[0])
    except IndexError:
        stock_list = db.Stock.select()[:]
        for s in stock_list:
            ticker_list.append(s.stock)
    print("[Command Volume Compare Handler] User asked for = " + str(ticker_list)[1:-1])
    combined_message = '(CurrentVolume - 21AverageVolume) / 21AverageVolume) * 100\n==========\n'
    for ticker in ticker_list:
        taHelper = TAHelper(ticker)
        index = taHelper.run_volume_compare_percentage_index()
        combined_message += '%s : %f%%\n' % (ticker, index)
    print("command_volume_compare_handler log = " + combined_message)
    update.message.reply_text(combined_message)

def set_telegram_bot(pony_db, token):
    global updater
    updater = Updater(token=token, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    global db
    db = pony_db
    start_handler = CommandHandler('start', start)
    ticker_history_handler = CommandHandler('ticker', command_ticker_history_handler, pass_args=True)
    date_history_handler = CommandHandler('date', command_date_history_handler, pass_args=True)
    volume_compare_handler = CommandHandler('volumediff', command_volume_compare_handler, pass_args=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ticker_history_handler)
    dispatcher.add_handler(date_history_handler)
    dispatcher.add_handler(volume_compare_handler)
    updater.start_polling()

@db_session
def send_message(message):
    telegram_user_list = db.TelegramUser.select()[:]
    for telegram_user in telegram_user_list:
        updater.bot.send_message(chat_id=telegram_user.chat_id, text=message)