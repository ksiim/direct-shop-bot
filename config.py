from dotenv import load_dotenv
import os

load_dotenv()  # Загрузка переменных из .env файла

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
REQS = os.getenv('REQS')
CHANNEL_TYPE = os.getenv('CHANNEL_TYPE')
BASE_NAME = os.getenv('BASE_NAME')
BASE_PHONE_NUMBER = os.getenv('BASE_PHONE_NUMBER')