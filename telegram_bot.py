###############################################################################
#                            RUN MAIN                                         #
###############################################################################

# setup
## pkg
import telebot
import logging
import datetime
import dateparser
import pymongo
from settings import config

## bot
bot = telebot.TeleBot(config.telegram_key)
dic_user = {}

## setup db
client = pymongo.MongoClient(config.mongodb_key)
db_name = "Telegram_DatesReminderBot"
collection_name = "users"
db = client[db_name][collection_name]

## logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



# /start
@bot.message_handler(commands=['start'])
def _start(message):
    ## reset
    dic_user["id"] = str(message.chat.id)
    db.delete_one({'id':dic_user["id"]})
    logging.info(str(message.chat.username)+" - "+str(message.chat.id)+" --- START")

    ## send first msg
    msg = "Hello "+str(message.chat.username)+\
          ", I'm a date reminder. Tell me birthdays and events to remind you. To learn how to use me, use \n/help"
    bot.send_message(message.chat.id, msg)



# /help
@bot.message_handler(commands=['help'])
def _help(message):
    msg = "Set an event, like someone's birthday, for example: \n\
            Nadia: Oct 25 \nAnd I'm gonna save the date and every Oct 25 I will remind you of Nadia's birthday. \n\
Save a date with \n/save \n\
You can always check for today's event with \n/check"
    bot.send_message(message.chat.id, msg)



# /save
@bot.message_handler(commands=['save'])
def _save(message):
    msg = "Set an event in the format 'month dd', for example: \n\
            xmas day: Dec 25 \n\
I also understand: \n\
today, tomorrow, in 3 days, in 1 week, in 6 months, yesterday, 3 days ago ... so you can do: \n\
            anniversary: tomorrow"
    message = bot.reply_to(message, msg)
    bot.register_next_step_handler(message, save_event)


def save_event(message):
    dic_user["id"] = str(message.chat.id)

    ## get text
    txt = message.text
    logging.info(str(message.chat.username)+" - "+str(message.chat.id)+" --- SAVE - "+txt)
    name, date = txt.split(":")[0].strip(), txt.split(":")[1].strip()

    ## check date
    date = dateparser.parse(date).strftime('%b %d')

    ## save
    lst_users = db.distinct(key="id")
    if dic_user["id"] not in lst_users:
        db.insert_one({"id":dic_user["id"], "events":{name:date}})
    else:
        dic_events = db.find_one({"id":dic_user["id"]})["events"]
        dic_events.update({name:date})
        db.update_one({"id":dic_user["id"]}, {"$set":{"events":dic_events}})
    
    ## send done
    msg = name+": "+date+" saved."
    bot.send_message(message.chat.id, msg)



# /check
@bot.message_handler(commands=['check'])
def _check(message):
    dic_user["id"] = str(message.chat.id) 

    ## error
    lst_users = db.distinct(key="id")
    if dic_user["id"] not in lst_users:
        msg = "First you need to save an event with \n/save"

    ## query
    else:
        dic_events = db.find_one({"id":dic_user["id"]})["events"]
        today = datetime.datetime.today().strftime('%b %d')
        logging.info(str(message.chat.username)+" - "+str(message.chat.id)+" --- CHECKING")
        res = [k for k,v in dic_events.items() if v == today]
        msg = "Today's events: "+", ".join(res) if len(res) > 0 else "No events today"
    
    bot.send_message(message.chat.id, msg)



# /view
@bot.message_handler(commands=['view'])
def _view(message):
    dic_user["id"] = str(message.chat.id) 

    ## error
    lst_users = db.distinct(key="id")
    if dic_user["id"] not in lst_users:
        msg = "You have no events. Save an event with \n/save"

    ## query
    else:
        dic_events = db.find_one({"id":dic_user["id"]})["events"]
        dic_events_sorted = {k:v for k,v in sorted(dic_events.items(), key=lambda item:item[0])}
        logging.info(str(message.chat.username)+" - "+str(message.chat.id)+" --- VIEW ALL")
        msg = "\n".join(k+": "+v for k,v in dic_events_sorted.items())
    
    bot.send_message(message.chat.id, msg)



# /delete
@bot.message_handler(commands=['delete'])
def _delete(message):
    ## ask name
    msg = "Tell me the event to Delete, for example: \n\
            xmas day \nAnd I'm gonna stop the reminder."
    message = bot.reply_to(message, msg)
    bot.register_next_step_handler(message, delete_event)


def delete_event(message):
    dic_user["id"] = str(message.chat.id)

    ## get text
    txt = message.text
    logging.info(str(message.chat.username)+" - "+str(message.chat.id)+" --- DELETE - "+txt)

    ## delete
    dic_events = db.find_one({"id":dic_user["id"]})["events"]
    dic_events.pop(txt)
    db.update_one({"id":dic_user["id"]}, {"$set":{"events":dic_events}})
    
    ## send done
    msg = txt+" deleted."
    bot.send_message(message.chat.id, msg)



# non-command message
@bot.message_handler(func=lambda m: True)
def chat(message):
    txt = message.text
    if any(x in txt.lower() for x in ["thank","thx","cool"]):
        msg = "anytime"
    elif any(x in txt.lower() for x in ["hi","hello","yo","hey"]):
        msg = "yo" if str(message.chat.username) == "none" else "yo "+str(message.chat.username)
    else:
        msg = "save a date with \n/save"
    bot.send_message(message.chat.id, msg)



# scheduler
def scheduler():
    lst_users = db.distinct(key="id")
    logging.info("--- SCHEDULER for "+str(len(lst_users))+" users ---")
    for user in lst_users:
        #res = requests.get("https://api.telegram.org/bot1494658770:"+config.telegram_key+"/sendMessage?chat_id="+user+"&text=yo")
        dic_events = db.find_one({"id":user})["events"]
        today = datetime.datetime.today().strftime('%b %d')
        res = [k for k,v in dic_events.items() if v == today]
        if len(res) > 0:
            msg = "Today's events: "+", ".join(res)
            bot.send_message(user, msg)



# run
if config.ENV == "DEV":
    bot.infinity_polling(True)  #bot.polling()


elif config.ENV == "PROD":
    import flask
    import threading

    app = flask.Flask(__name__)

    @app.route('/'+config.telegram_key, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.stream.read().decode("utf-8"))])
        return "!", 200

    @app.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url=config.webhook+config.telegram_key)
        return 'Chat with the Bot  <a href ="https://t.me/DatesReminderBot">here</a> \
          or   Check the project code <a href ="https://github.com/mdipietro09/Bot_TelegramDatesReminder">here</a>', 200

    if __name__ == "__main__":
        print("---", datetime.datetime.now().strftime("%H:%M"), "---")
        #if datetime.datetime.now().strftime("%H:%M") in ["05:00","05:01","06:00","06:01","07:00","07:01"]:
        threading.Thread(target=scheduler).start()
        app.run(host=config.host, port=config.port)