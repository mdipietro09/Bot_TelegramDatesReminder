###############################################################################
#                            RUN MAIN                                         #
###############################################################################

import telebot
import logging
import datetime
from keys import telegram_key

bot = telebot.TeleBot(telegram_key)
dic_user = {}



# /start
@bot.message_handler(commands=['start'])
def _start(message):
    ## register user
    user_id = str(message.chat.id)
    dic_user["id"] = user_id
    logging.info("Setting up User "+dic_user["id"])

    ## send first msg
    msg = "Hello "+str(message.chat.username)+\
          ", I'm a date reminder. Tell me birthdays and events to remind you. To learn how to use me, use \n/help"
    bot.send_message(message.chat.id, msg)



# /help
@bot.message_handler(commands=['help'])
def _help(message):
    msg = "Set a person's date (yyyy-mm-dd), for example: \n\
            John Smith:1990-10-31 \nAnd I'm gonna save the date and every 31/10 I will remind you of John's birthday. \n\
You can always check for today's event with \n/check"
    bot.send_message(message.chat.id, msg)



# /save
@bot.message_handler(commands=['save'])
def _save(message):
    ## ask name
    msg = "Set a person's date (yyyy-mm-dd), for example: \n\
            John Smith: 1990-10-31"
    message = bot.reply_to(message, msg)
    bot.register_next_step_handler(message, save_birthday)


def save_birthday(message):
    ## get text
    txt = message.text
    logging.info("Chat "+dic_user["id"]+" - Input: "+txt)
    name, date = txt.split(":")[0].strip(), txt.split(":")[1].strip()
    
    ## save
    if "birthdays" not in dic_user.keys():
        dic_user["birthdays"] = {}
    dic_user["birthdays"].update({name:date})
    
    ## send done
    msg = name+"'s birthday saved."
    bot.send_message(message.chat.id, msg)



# /check
@bot.message_handler(commands=['check'])
def _check(message): 
    ## error
    if "birthdays" not in dic_user.keys():
        msg = "First you need to save birthdays with \n/save"

    ## query
    else:  
        today = datetime.datetime.today()
        logging.info(today.strftime("%m-%d"))
        res = [k for k,v in dic_user["birthdays"].items() if datetime.datetime.strptime(v,'%Y-%m-%d').strftime("%m-%d") == today.strftime("%m-%d")]
        msg = "Today's birthday: "+", ".join(res) if len(res) > 0 else "No birthdays today"
    
    bot.send_message(message.chat.id, msg)



# non-command message
@bot.message_handler(func=lambda m: True)
def chat(message):
    txt = message.text
    if any(x in txt.lower() for x in ["thank","thx","cool"]):
        msg = "anytime"
    else:
        msg = "..."
    bot.send_message(message.chat.id, msg)



# run
bot.polling()