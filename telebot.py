import os
import logging
import datetime
from telegram import ext, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from validate_email import validate_email
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
handler = logging.FileHandler('logs/bot.log', 'w', 'utf-8')
handler.setFormatter(formatter)
logger.addHandler(handler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
client = None
database = None
weekdays_dictionary = {"0": "Segunda-Feira", "1": "Terça-Feira", "2": "Quarta-Feira", "3": "Quinta-Feira", "4": "Sexta-Feira", "5": "Sábado", "6": "Domingo"}
command_list_message="\nLista de comandos:\
        \n*/cadastro* ou *cadastro* - visualizar seus dados cadastros em meu banco de dados\
        \n*/email (EMAIL_DE_CADASTRO)* - atualizar o email cadastrado\
        \n*/cadastrar* - realizar um pré cadastro com suas informações, recuperadas pelo telegram\
        \n*/planilha (NOME_NA_PLANILHA)* - realiza o cadastro de seu nome identificador na planilha de café da manhã, note que o essa informação deve ser igual a escrita na planilha\
        \n*/telegram (on|off)* - altera configuração de alerta no telegram, *on* para começar a receber o alerta ou *off* para parar de receber o alerta\
        \n*/limpar_email* - remove email do cadastro, com isso você para de receber alertas no email\
        \n*/dia* ou *dia* - atualizar o dia da semana que deseja receber as notificações.\
        \n*/ajuda* ou *ajuda* - visualizar a lista de comandos novamente.\
        "

def getDatabase():
    global client
    global database
    if(client == None):
        client = MongoClient(os.environ['MONGO_URL'])
    if(database == None):
        database = client['alerts']
    return database
    
def getUserCollection():
    db = getDatabase()
    return db['users']

#client.close()
def formatUserData(user):
    global weekdays_dictionary
    return "Nome: {}\
        \nEmail: {}\
        \nIdentificador na planilha: {}\
        \nNotificação no Telegram: {}\
        \nDia da semana para notificação: {}\
        \nCriado em: {}\
        \nAtualizado em: {}".format(user['name'], 
        (user['email'] if 'email' in user and user['email'] != None else ""),
        (user['spreadsheet_identifier'] if 'spreadsheet_identifier' in user and user['spreadsheet_identifier'] != None else ""),
        ("Ativo" if 'alert_telegram' in user and user['alert_telegram'] else "Inativo"),
        (weekdays_dictionary.get(user['alert_weekday']) if 'alert_weekday' in user and user['alert_weekday'] != None else ""),
        (user['created_at'].strftime("%d/%m/%Y %H:%M:%S") if 'created_at' in user and user['created_at'] != None else ""),
        (user['updated_at'].strftime("%d/%m/%Y %H:%M:%S") if 'updated_at' in user and user['updated_at'] != None else "")
    )

def signup(bot, update):
    logger.info('Signing up user {}, chat_id {}'.format(update.message.from_user.first_name,update.message.chat_id))
    message = "Cadastro realizado com sucesso!"
    user_collection = getUserCollection()
    user = user_collection.find_one({"_id": str (update.message.chat_id)})
    if(user == None):
        user = {
            "_id": str(update.message.chat_id),
            "name":update.message.from_user.first_name,
            "spreadsheet_identifier":update.message.from_user.first_name,  
            "chat_id": str(update.message.chat_id),
            "alert_telegram": False,
            "alert_weekday": 3,
            "alert_hour": "15:00",
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
        }
        user_id = user_collection.insert_one(user).inserted_id
        if(user_id == None):
            message = "Não foi possível cadastrar usuário."
    else:
        message = "Já existe um cadastro"
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )

def register(bot, update):
    logger.info('Query chat_id {} register'.format(update.message.chat_id))
    user_collection = getUserCollection()
    user = user_collection.find_one({"_id": str (update.message.chat_id)})
    message = "Usuário não cadastrado."
    if(user != None):
        message = formatUserData(user)
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )

def hello(bot, update):
    global command_list_message
    welcome = "Olá, sou um bot de cadastro para possibilitar o envio de alertas para você." + command_list_message
    logger.info('User {}, chat_id {} started to chat with bot'.format(update.message.from_user.first_name,update.message.chat_id))
    bot.send_message(
        chat_id=update.message.chat_id,
        text=welcome,
        parse_mode='Markdown'
    )

def update_email(bot, update, args):
    message = "E-mail atualizado com sucesso. A partir de agora você começará a receber alertas em seu email cadastro, caso deseje parar de receber utilize o comando /clear_email"
    if(args != None and len(args) > 0 and args[0] != None and args[0] != ""):
        logger.info('Updating email to user {}, new email {}'.format(update.message.chat_id, args[0]))
        is_valid = validate_email(args[0])
        if(is_valid):
            user_collection = getUserCollection()
            result = user_collection.update_one({"_id": str (update.message.chat_id)},  {"$set": {"email": args[0], "updated_at": datetime.datetime.now()}})
            if(result.modified_count <= 0):
                message = "Não foi encontrar o cadastro a ser atualizado, por favor tente novamente mais tarde."
        else:
            message = "E-mail informado não é válido."
    else:
        message = "É necessário informar um email para atualizar o cadastro."
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )

def register_spreadsheet_name(bot, update, args):
    message = "Identificador da planilha atualizado com sucesso!"
    if(args != None and len(args) > 0 and args[0] != None and args[0] != ""):
        new_identifier = " ".join(args)
        logger.info('Updating user {} spreadsheet user identifier to {}'.format(update.message.chat_id, new_identifier))
        user_collection = getUserCollection()
        result = user_collection.update_one({"_id": str (update.message.chat_id)},  {"$set": {"spreadsheet_identifier": new_identifier, "updated_at": datetime.datetime.now()}})
        if(result.modified_count <= 0):
            message = "Não foi encontrar o cadastro a ser atualizado, por favor tente novamente mais tarde."
    else:
        message = "Para utilizar esse comando é necessário informar um texto."
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )

def change_alert_telegram(bot, update, args):
    message = "Configuração atualizada."
    if(args != None and len(args) > 0 and args[0] != None and args[0] != "" and (args[0] == "on" or args[0] == "off")) :
        user_collection = getUserCollection()
        result = user_collection.update_one({"_id": str (update.message.chat_id)},  {"$set": {"alert_telegram": args[0] == "on", "updated_at": datetime.datetime.now()}})
        if(result.modified_count <= 0):
            message = "Não foi encontrar o cadastro a ser atualizado, por favor tente novamente mais tarde."
    else:
        message = "Opção informada é inválida, por favor envie o comando novamente com a opção on para começar a receber o alerta ou off para parar de receber o alerta"
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )

def clear_email(bot, update):
    message = "E-mail removido com sucesso!"
    logger.info('Clearing user {} email to user'.format(update.message.chat_id))
    user_collection = getUserCollection()
    result = user_collection.update_one({"_id": str (update.message.chat_id)},  {"$set": {"email": "", "updated_at": datetime.datetime.now()}})
    if(result.modified_count <= 0):
        message = "Não foi encontrar o cadastro a ser atualizado, por favor tente novamente mais tarde."
    bot.send_message(
        chat_id=update.message.chat_id,
        text=message
    )
    
def help(bot, update):
    global command_list_message
    help_message = "Ajuda." + command_list_message
    bot.send_message(
        chat_id=update.message.chat_id,
        text=help_message,
        parse_mode='Markdown'
    )

def text_decoder(bot, update):
    message = ""
    user_text = update.message.text.casefold()
    logger.info("User sent text: {}".format(user_text))
    if user_text == "cadastro":
        register(bot, update)
    elif user_text == "cadastrar":
        signup(bot, update)
    elif user_text == "ajuda":
        help(bot, update)
    elif user_text == "dia":
        show_week_day_keyboard(bot, update)
    else:
        is_valid = validate_email(update.message.text)
        if(is_valid):
            user_collection = getUserCollection()
            user = user_collection.find_one({"_id": str (update.message.chat_id)})
            if(user != None):
                if(user['email'] != None):
                    message = "Usuário já possui um e-mail cadastrado! Se deseja atualizar o email, utilize o comando: /email NOVO_EMAIL"
                else:
                    user_collection.update_one({"_id": str (update.message.chat_id)},  {"$set": {"email": update.message.text, "updated_at": datetime.datetime.now()}})
                    message = "E-mail cadastrado com sucesso!"
            else:
                message = "Não foi possível atualizar e-mail, por favor inicie o cadastro com /cadastro"
        else:
            message = "😬 Desculpe ainda não aprendi a responder sua mensagem"
        bot.send_message(
            chat_id=update.message.chat_id,
            text=message
        )

def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

def update_notification_weekday(user_id, choosen_weekday):
    global weekdays_dictionary
    status = True
    message = "Configuração atualizada."
    if(choosen_weekday != None and choosen_weekday != "" and weekdays_dictionary.get(choosen_weekday) != None) :
        user_collection = getUserCollection()
        result = user_collection.update_one({"_id": str (user_id)},  {"$set": {"alert_weekday": choosen_weekday, "updated_at": datetime.datetime.now()}})
        if(result.modified_count <= 0):
            status = False
            message = "Não foi encontrar o cadastro a ser atualizado, por favor tente novamente mais tarde."
    else:
        status = False
        message = "Opção informada é inválida."
    return message, status

def show_week_day_keyboard(bot, update):
    button_list = [
        InlineKeyboardButton("Segunda-Feira", callback_data="weekday=0"),
        InlineKeyboardButton("Terça-Feira", callback_data="weekday=1"),
        InlineKeyboardButton("Quarta-Feira", callback_data="weekday=2"),
        InlineKeyboardButton("Quinta-Feira", callback_data="weekday=3"),
        InlineKeyboardButton("Sexta-Feira", callback_data="weekday=4"),
        InlineKeyboardButton("Sábado", callback_data="weekday=5"),
        InlineKeyboardButton("Domingo", callback_data="weekday=6")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Escolha um dia da semana para atualizar",
        reply_markup=reply_markup
    )

def callback_handler(bot, update):
    status = False
    send_message = False
    message = "Configuração atualizada."
    query = update.callback_query
    if("weekday" in query.data):
        message, status = update_notification_weekday(query.message.chat.id,query.data.replace("weekday=", ""))
        send_message = status
    elif("spreadsheetName" in query.data):
        message = "Nada foi feito!"
        status = True
        send_message = True
    elif(query.data == "exitNameCallback"):
        status = True
    else:
        message = "Não foi possível recuperar informação, por favor tente mais tarde."
    if(send_message):
        bot.answer_callback_query(
            callback_query_id=query.id,
            text=message
        )
        bot.send_message(
            chat_id=query.message.chat.id,
            text=message
        )
    if(status):
        bot.deleteMessage(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )

def show_names_suggestion(bot, update):
    names = ["1 - Fulando", "2 - Ciclano", "3 - João"]
    button_list = []
    footer_list = [InlineKeyboardButton("Fechar", callback_data="exitNameCallback")]
    for name in names:
        button_list.append(InlineKeyboardButton(name, callback_data="spreadsheetName={}".format(name)))
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2, footer_buttons=footer_list))
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Sugestões de nomes, caso seu identificador não esteja na lista ou deseje digitar manualmente utilize o comando /planilha (NOME_NA_PLANILHA)",
        reply_markup=reply_markup
    )

def main():
    updater = ext.Updater(os.environ['TELEGRAM_BOT_KEY'])
    dispatcher = updater.dispatcher
    dispatcher.add_handler(ext.CommandHandler('cadastro', register))
    dispatcher.add_handler(ext.CommandHandler('start', hello))
    dispatcher.add_handler(ext.CommandHandler('cadastrar', signup))
    dispatcher.add_handler(ext.CommandHandler('email', update_email, pass_args=True))
    dispatcher.add_handler(ext.CommandHandler('planilha', register_spreadsheet_name, pass_args=True))
    dispatcher.add_handler(ext.CommandHandler('telegram', change_alert_telegram, pass_args=True))
    dispatcher.add_handler(ext.CommandHandler('limpar_email', clear_email))
    dispatcher.add_handler(ext.CommandHandler('ajuda', help))
    dispatcher.add_handler(ext.CommandHandler('dia', show_week_day_keyboard))
    dispatcher.add_handler(ext.CommandHandler('teste', show_names_suggestion))
    dispatcher.add_handler(ext.CallbackQueryHandler(callback_handler))
    dispatcher.add_handler(ext.MessageHandler(ext.Filters.text, text_decoder))
    logger.info("Starting polling")
    updater.start_polling()
    logger.info("Bot in idle, awaiting users messages")
    updater.idle()

if __name__ == '__main__':
    print("press CTRL + C to cancel.")
    main()