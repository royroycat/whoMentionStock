from telegram.ext import Updater
from telegram.ext import CommandHandler
from datetime import datetime
from pony.orm import *
import telegram
from helpers import ark_helper

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
def command_ark_history_handler(update, context):
    try:
        ticker = context.args[0]
    except IndexError:
        ticker = "TSLA"
    print("[Command ARK History Handler] User asked for = " + ticker)
    trading_infos = ark_helper.get_ticker_history(ticker)
    company = list(trading_infos)[0].company.replace('\n', ' ')
    combined_message = f"{ticker} ({company}) :\n"
    for info in trading_infos:
        date = info.date.strftime("%d/%m/%Y")
        combined_message += f"{date} {info.fund} {info.direction} {info.shares} {info.etf_percent}\n"
    print("command_ark_history_handler log = " + combined_message)
    update.message.reply_text(combined_message)

def set_telegram_bot(pony_db, token):
    global updater
    updater = Updater(token=token, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    global db
    db = pony_db
    start_handler = CommandHandler('start', start)
    ark_history_handler = CommandHandler('ark_history', command_ark_history_handler, pass_args=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ark_history_handler)
    updater.start_polling()
    updater.idle()

@db_session
def send_message(message):
    telegram_user_list = db.TelegramUser.select()[:]
    for telegram_user in telegram_user_list:
        updater.bot.send_message(chat_id=telegram_user.chat_id, text=message)