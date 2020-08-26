from telegram.ext import Updater
from telegram.ext import CommandHandler
from datetime import datetime
from pony.orm import *
import telegram

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


def set_telegram_bot(pony_db, token):
    global updater
    updater = Updater(token=token, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    global db
    db = pony_db
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    updater.start_polling()
    updater.idle()

@db_session
def send_message(message):
    telegram_user_list = db.TelegramUser.select()[:]
    for telegram_user in telegram_user_list:
        updater.bot.send_message(chat_id=telegram_user.chat_id, text=message)