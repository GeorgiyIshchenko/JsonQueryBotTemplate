import os

from telegram.ext import Application, CommandHandler

from dotenv import load_dotenv

from src.query_bot import QueryBot

if __name__ == '__main__':
    load_dotenv()
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    application = Application.builder().token(BOT_TOKEN).build()

    QueryBot.file_path = "bot.json"
    QueryBot.app = application
    QueryBot.init()

    application.add_handler(CommandHandler('start', QueryBot.base_handler))

    application.run_polling()
