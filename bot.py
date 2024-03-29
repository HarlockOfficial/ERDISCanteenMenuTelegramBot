"""
Telegram bot
"""
import os
import datetime
import logging
from typing import List

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, ContextTypes, Filters
from dotenv import load_dotenv

import data_base as db
import menu as menu_module

load_dotenv()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher


def save_user(update: Update, _: ContextTypes):
    """
    Save user to database
    """
    logger.info("Adding user: %s", update.effective_user.username)
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
            'canteen_list': []
        })
        update.message.reply_text(f'Hello, {update.effective_user.first_name}!', parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(f'Hello again, {update.effective_user.first_name}!', parse_mode=ParseMode.HTML)
    logger.info("Added user: %s", update.effective_user.username)
    db.close_connection(mongo_client)


def subscribe(update: Update, _: ContextTypes):
    """
    Subscribe user to daily updates
    """
    logger.info("Subscribing user: %s", update.effective_user.username)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.update_one({'id':update.effective_user.id}, {'$set': {'send_daily_updates': True, 'canteen_list': []}})
    update.message.reply_text(f'You have been subscribed to daily updates, {update.effective_user.first_name}!\nPlease save your favourite canteen(s) to receive daily updates.\nTo do so, send /save_canteen_to_favourite followed by the names of your favourite canteens.', parse_mode=ParseMode.HTML)
    db.close_connection(mongo_client)
    logger.info("Subscribed user: %s", update.effective_user.username)


def unsubscribe(update: Update, _: ContextTypes):
    """
    Unsubscribe user from daily updates
    """
    logger.info("Unsubscribing user: %s", update.effective_user.username)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.update_one({'id':update.effective_user.id}, {'$set': {'send_daily_updates': False, 'canteen_list': []}})
    update.message.reply_text(f'You have been unsubscribed from daily updates, {update.effective_user.first_name}!', parse_mode=ParseMode.HTML)
    db.close_connection(mongo_client)
    logger.info("Unsubscribed user: %s", update.effective_user.username)


def delete_user(update: Update, _: ContextTypes):
    """
    Delete user from database
    """
    logger.info("Deleting user: %s", update.effective_user.username)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    collection.delete_one({'id': update.effective_user.id})
    update.message.reply_text(f'Goodbye, {update.effective_user.first_name}!', parse_mode=ParseMode.HTML)
    db.close_connection(mongo_client)
    logger.info("Deleted user: %s", update.effective_user.username)


def get_today_menu():
    """
    Get today's menu from database
    """
    logger.info("Getting today menu")
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_MENU_COLLECTION')]
    menu = list(collection.find({'date': datetime.date.today().isoformat()}))
    db.close_connection(mongo_client)
    if len(menu) == 0:
        menu_module.init_menu()
        menu = get_today_menu()
    logger.info("Got today menu")
    return menu


def get_today_menu_string(menu = None, canteen_names: List[str] = None) -> List[str]:
    """
    Get today's menu as a string
    """
    logger.info("Getting today menu string")
    if menu is None:
        menu = get_today_menu()
    if canteen_names is not None and len(canteen_names) > 0:
        menu = filter(lambda x: x['canteen'].lower() in [x.lower() for x in canteen_names], menu)
    text = ['Today\'s menu:\n']
    for item in menu:
        tmp_text = f' Canteen <b>{item["canteen"].title()}</b>:\n'
        if item['time']['Pranzo']['IsOpen']:
            tmp_text += '\t<b>Lunch</b>:\n'
            for course in item["menu"]["Pranzo"]:
                tmp_text += f'\t\t<b>{course.title()}</b>:\n'
                for plate in item['menu']['Pranzo'][course]:
                    tmp_text += f'\t\t\t{plate.title()}\n'
        else:
            tmp_text += '\t<b>Lunch</b>: Closed\n'
        if item['time']['Cena']['IsOpen']:
            tmp_text += '\t<b>Dinner</b>:\n'
            for course in item["menu"]["Cena"]:
                tmp_text += f'\t\t<b>{course}</b>:\n'
                for plate in item['menu']['Cena'][course]:
                    tmp_text += f'\t\t\t{plate.title()}\n'
        else:
            tmp_text += '\tDinner: Closed\n'
        text.append(tmp_text)
    if len(text) <= 1:
        text = ['No menu available for the specified canteens']
    logger.info("Got today menu string")
    return text


def today_menu(update: Update, _: ContextTypes):
    """
    Send today's menu
    """
    logger.info("Sending today menu to user: %s", update.effective_user.username)
    msg_content = update.message.text.split(' ')
    text = get_today_menu_string(canteen_names=msg_content[1:])
    for msg in text:
        update.message.reply_text(text=msg, parse_mode=ParseMode.HTML)
    logger.info("Sent today menu to user: %s", update.effective_user.username)


def send_daily_updates(context: ContextTypes):
    """
    Send daily updates to users
    """
    logger.info('Start sending daily updates')
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    users = list(collection.find({'send_daily_updates': True}))
    db.close_connection(mongo_client)
    for user in users:
        menu = get_today_menu_string(canteen_names=user['canteen_list'])
        for msg in menu:
            context.bot.send_message(chat_id=user['chat_id'], text=msg, parse_mode=ParseMode.HTML)
    logger.info('Completed sending daily updates')


def get_user_canteen_list_from_db(user_id):
    """
    Get user's canteen list from database
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    user = collection.find_one({'id': user_id})
    db.close_connection(mongo_client)
    return user["canteen_list"]


def get_user_canteen_list(update: Update, _: ContextTypes):
    """
    Get user's canteen list
    """
    logger.info("Getting canteen list for user: %s", update.effective_user.username)
    canteen_list = get_user_canteen_list_from_db(update.effective_user.id)
    update.message.reply_text(get_canteen_list_string(canteen_list), parse_mode=ParseMode.HTML)
    logger.info("Got canteen list for user: %s", update.effective_user.username)


def get_canteen_list_string(canteen_list: List[str]) -> str:
    """
    Get canteen list as a string
    """
    logger.info("Getting canteen list string")
    text = 'Canteen list:\n'
    for canteen in canteen_list:
        text += f'\t<b>{canteen.title()}</b>\n'
    logger.info("Got canteen list string")
    return text

def add_canteen_to_user_list(update: Update, _: ContextTypes):
    """
    Add canteen to user's canteen list
    """
    logger.info("Adding canteen list to user: %s", update.effective_user.username)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    user = collection.find_one({'id': update.effective_user.id})
    canteen_list = user['canteen_list']
    msg_content = update.message.text.split(' ')
    msg_content = list(filter(lambda x: x.lower() in [canteen.value.lower() for canteen in menu_module.Canteen], [x.lower() for x in msg_content[1:]]))
    canteens_to_add = list(set(msg_content) - set(canteen_list))
    if len(canteens_to_add) <= 0:
        update.message.reply_text('No canteens added, please specify at least one', parse_mode=ParseMode.HTML)
        db.close_connection(mongo_client)
        logger.info("No canteens added to user: %s", update.effective_user.username)
        return
    canteen_list.extend(canteens_to_add)
    collection.update_one({'id': update.effective_user.id}, {'$set': {'canteen_list': canteen_list}})
    db.close_connection(mongo_client)
    update.message.reply_text(get_canteen_list_string(canteen_list), parse_mode=ParseMode.HTML)
    logger.info("Added canteen list to user: %s", update.effective_user.username)


def remove_canteen_from_user_list(update: Update, _: ContextTypes):
    """
    Remove canteen from user's canteen list
    """
    logger.info("Removing canteen list from user: %s", update.effective_user.username)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_USER_COLLECTION')]
    user = collection.find_one({'id': update.effective_user.id})
    canteen_list = user['canteen_list']
    msg_content = update.message.text.split(' ')[1:]
    if len(msg_content) <= 0:
        update.message.reply_text('No canteens removed, specify at least one canteen to remove', parse_mode=ParseMode.HTML)
        return
    canteen_list = list(filter(lambda x: x.lower() not in [canteen.lower() for canteen in msg_content], canteen_list))
    collection.update_one({'id': update.effective_user.id}, {'$set': {'canteen_list': canteen_list}})
    db.close_connection(mongo_client)
    update.message.reply_text(get_canteen_list_string(canteen_list), parse_mode=ParseMode.HTML)
    logger.info("Removed canteen list from user: %s", update.effective_user.username)


def get_canteen(canteen_name: str) -> dict:
    """
    Get canteen from database
    """
    logger.info("Getting from database canteen: %s", canteen_name)
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client)
    collection = data_base[os.getenv('DB_MENU_COLLECTION')]
    canteen = collection.find_one({'canteen': canteen_name.lower()})
    db.close_connection(mongo_client)
    logger.info("Got from database canteen: %s", canteen)
    return canteen


def get_today_time_string(canteen_names: List[str] = None) -> str:
    """
    Get today time string
    """
    text = ""
    if canteen_names is None or len(canteen_names)<=0:
        text = "Since no canteen has been specified, here you have the full list\n"
        canteen_names = [canteen.value for canteen in menu_module.Canteen]
    text = []
    for canteen in canteen_names:
        canteen = get_canteen(canteen)
        if canteen is None:
            continue
        tmp_text = f'Canteen <b>{canteen["canteen"].title()}</b>:\n'
        if canteen['time']['Pranzo']['IsOpen']:
            tmp_text += f'\t<b>Lunch</b>: {canteen["time"]["Pranzo"]["OpenTime"]} - {canteen["time"]["Pranzo"]["CloseTime"]}\n'
        else:
            tmp_text += '\t<b>Lunch</b>: Closed\n'
        if canteen['time']['Cena']['IsOpen']:
            tmp_text += f'\t<b>Dinner</b>: {canteen["time"]["Cena"]["OpenTime"]} - {canteen["time"]["Cena"]["CloseTime"]}\n'
        else:
            tmp_text += '\t<b>Dinner</b>: Closed\n'
        text.append(tmp_text)
    if len(text)<=0:
        text = ["No valid canteens found"]
    return text

def canteen_time(update: Update, _: ContextTypes):
    """
    Get canteen time
    """
    logger.info("Getting canteen time for user: %s", update.effective_user.username)
    try:
        msg_content = update.message.text.split(' ')
    except AttributeError:
        return
    text = get_today_time_string(msg_content[1:])
    for msg in text:
        update.message.reply_text(text=msg, parse_mode=ParseMode.HTML)
    logger.info("Got canteen time for user: %s", update.effective_user.username)


def my_canteens_menu(update: Update, _: ContextTypes):
    """
    Get favourite canteens menu
    """
    logger.info("Getting favourite canteens menu for user: %s", update.effective_user.username)
    canteen_list = get_user_canteen_list_from_db(update.effective_user.id)
    text = get_today_menu_string(canteen_names=canteen_list)
    for msg in text:
        update.message.reply_text(text=msg, parse_mode=ParseMode.HTML)
    logger.info("Got favourite canteens menu for user: %s", update.effective_user.username)


def my_canteens_time(update: Update, _: ContextTypes):
    """
    Get favourite canteens time
    """
    logger.info("Getting favourite canteens time for user: %s", update.effective_user.username)
    canteen_list = get_user_canteen_list_from_db(update.effective_user.id)
    text = get_today_time_string(canteen_names=canteen_list)
    for msg in text:
        update.message.reply_text(text=msg, parse_mode=ParseMode.HTML)
    logger.info("Got favourite canteens time for user: %s", update.effective_user.username)


def available_canteen_list(update: Update, _: ContextTypes):
    """
    Get canteen list
    """
    logger.info("Getting available canteens for user: %s", update.effective_user.username)
    update.message.reply_text(get_canteen_list_string([canteen.value for canteen in menu_module.Canteen]), parse_mode=ParseMode.HTML)
    logger.info("Got available canteens for user: %s", update.effective_user.username)


def bot_credits(update: Update, _: ContextTypes):
    """
    Send credits message
    """
    logger.info("Sending credits to user: %s", update.effective_user.username)
    text = 'Credits:\n'
    text += 'The full source code of this bot is available at:\n'
    text += 'https://github.com/HarlockOfficial/ERDISCanteenMenuTelegramBot\n'
    text += 'Contributions are well accepted.\n'
    text += 'This bot was created for fun by HarlockOfficial\n'
    text += 'GitHub: https://github.com/HarlockOfficial\n'
    text += 'Telegram: @HarlockOfficial\n'
    text += 'This bot is not affiliated with the University of Camerino nor the ERDIS Marche\n'
    text += 'The ERDIS Marche is not responsible for the content of this bot\n'

    update.message.reply_text(text, parse_mode=ParseMode.HTML)
    logger.info("Sent credits to user: %s", update.effective_user.username)


def bot_help(update: Update, _: ContextTypes):
    """
    Send help message
    """
    logger.info("Sending help to user: %s", update.effective_user.username)
    text = 'Help:\n'
    text += '/start - Start the bot\n'
    text += '/subscribe - Subscribe to daily updates\n'
    text += '/unsubscribe - Unsubscribe from daily updates\n'
    text += '/stop - Stop the bot\n'
    text += '/menu - Get today\'s menu for the specified canteen(s)\n'
    text += '/favourite_canteen_list - Get your favourite canteen(s) list\n'
    text += '/save_canteen_to_favourite - Add one or more canteens to your favourite canteen list\n'
    text += '/remove_canteen_from_favourite - Remove one or more canteens from your favourite canteen list\n'
    text += '/canteen_time - Get specified canteen(s) time\n'
    text += '/favourite_canteen_menu - Get your canteen(s) daily menu\n'
    text += '/favourite_canteen_time - Get your canteen(s) time\n'
    text += '/available_canteen_list - Get the names of available canteens\n'
    text += '/credits - Get credits\n'
    text += '/help - Shows this message\n'
    text += '/restart - Updates the bot source code from the related github branch, then restarts it'
    text += 'Example:\n'
    text += '\tThe following command will send you today\'s menu for canteen1 and canteen2:\n'
    text += '\t\t/menu canteen1 canteen2\n'
    text += '\tThe following command will add canteen1 and canteen2 to your favourite canteens list, so you will receive daily updates also for those two:\n'
    text += '\t\t/save_canteen_to_favourite canteen1 canteen2\n'
    text += '\tThe following command will show canteen1 and canteen2 open and close time for lunch and dinner:\n'
    text += '\t\t/canteen_time canteen1 canteen2\n'

    update.message.reply_text(text, parse_mode=ParseMode.HTML)
    logger.info("Sent help to user: %s", update.effective_user.username)


def unknown(update: Update, _: ContextTypes):
    """
    Function called when an unknown command is sent
    """
    logger.info("Received unknown command from user: %s", update.effective_user.username)
    update.message.reply_text("Sorry, I didn't understand.", parse_mode=ParseMode.HTML)


def restart(update: Update, _: ContextTypes):
  logger.info("Restarting the bot")
  import git
  g = git.cmd.Git('./')
  g.pull()
  logger.info("finished pulling updates")
  logger.info("killing bot")
  import os
  import signal
  os.kill(os.getpid(), signal.SIGINT)


def set_handlers():
    """
    Set handlers for the bot
    """
    logger.info("Setting handlers")
    dispatcher.add_handler(CommandHandler("start", save_user))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("stop", delete_user))
    dispatcher.add_handler(CommandHandler("menu", today_menu))
    dispatcher.add_handler(CommandHandler("favourite_canteen_list", get_user_canteen_list))
    dispatcher.add_handler(CommandHandler("save_canteen_to_favourite", add_canteen_to_user_list))
    dispatcher.add_handler(CommandHandler("remove_canteen_from_favourite", remove_canteen_from_user_list))
    dispatcher.add_handler(CommandHandler("canteen_time", canteen_time))
    dispatcher.add_handler(CommandHandler("favourite_canteen_menu", my_canteens_menu))
    dispatcher.add_handler(CommandHandler("favourite_canteen_time", my_canteens_time))
    dispatcher.add_handler(CommandHandler("available_canteen_list", available_canteen_list))
    dispatcher.add_handler(CommandHandler("credits", bot_credits))
    dispatcher.add_handler(CommandHandler("help", bot_help))
    dispatcher.add_handler(CommandHandler("restart", restart))
    dispatcher.add_handler(MessageHandler(Filters.command | Filters.text, unknown))
    logger.info("Set handlers")


def main():
    """
    Main function
    """
    logger.info('Starting bot...')
    set_handlers()
    j = updater.job_queue
    # server is 1 hh behind, so updates are sent at 9:00 am
    j.run_daily(send_daily_updates, time=datetime.time(hour=8, minute=0, second=0))
    updater.start_polling()
    logger.info('Bot started')
    updater.idle()


if __name__ == '__main__':
    main()
