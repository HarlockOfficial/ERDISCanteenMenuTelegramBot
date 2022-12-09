"""
Telegram bot
"""
import os
import datetime

import data_base as db
from telegram import Update
from telegram.ext import Updater, CommandHandler, ContextTypes
from dotenv import load_dotenv


load_dotenv()


updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher


async def save_user(update: Update, context: ContextTypes):
    """
    Save user to database
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    if collection.count_documents({'id': update.effective_user.id}) == 0:
        collection.insert_one({
            'id': update.effective_user.id,
            'first_name': update.effective_user.first_name,
            'last_name': update.effective_user.last_name,
            'username': update.effective_user.username,
            'chat_id': update.effective_chat.id,
            'send_daily_updates': False,
        })
        update.message.reply_text(f'Hello, {update.effective_user.first_name}!')
    else:
        update.message.reply_text(f'Hello again, {update.effective_user.first_name}!')
    db.close_connection(mongo_client)


async def subscribe(update: Update, context: ContextTypes):
    """
    Subscribe user to daily updates
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.update_one({'id':update.effective_user.id}, {'$set': {'send_daily_updates': True}})
    update.message.reply_text(f'You have been subscribed to daily updates, {update.effective_user.first_name}!')
    db.close_connection(mongo_client)


async def unsubscribe(update: Update, context: ContextTypes):
    """
    Unsubscribe user from daily updates
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.update_one({'id':update.effective_user.id}, {'$set': {'send_daily_updates': False}})
    update.message.reply_text(f'You have been unsubscribed from daily updates, {update.effective_user.first_name}!')
    db.close_connection(mongo_client)


async def delete_user(update: Update, context: ContextTypes):
    """
    Delete user from database
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.delete_one({'id': update.effective_user.id})
    update.message.reply_text(f'Goodbye, {update.effective_user.first_name}!')
    db.close_connection(mongo_client)


async def today(update: Update, context: ContextTypes):
    """
    Send today's news
    """
    # TODO implement, method stub
    text = 'Today'
    update.message.reply_text(text)


async def send_daily_updates(context: ContextTypes):
    """
    Send daily updates to users
    """
    # TODO implement, method stub
    data_base = db.get_data_base()
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    users = collection.find({'send_daily_updates': True})
    for user in users:
        text = 'Daily update'
        context.bot.send_message(chat_id=user['chat_id'], text=text)


async def help(update: Update, context: ContextTypes):
    """
    Send help message
    """
    # TODO implement, method stub
    text = 'Help'
    update.message.reply_text(text)


def set_handlers():
    """
    Set handlers for the bot
    """
    dispatcher.add_handler(CommandHandler("start", save_user))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("stop", delete_user))
    dispatcher.add_handler(CommandHandler("today", today))
    dispatcher.add_handler(CommandHandler("help", help))


def main():
    """
    Main function
    """
    set_handlers()
    j = updater.job_queue
    j.run_daily(send_daily_updates, time=datetime.time(hour=9, minute=0, second=0))
    updater.start_polling()


if __name__ == '__main__':
    main()
