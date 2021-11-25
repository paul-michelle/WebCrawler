"""Set default values of the main constants.

All of the constants are allowed to be set via commandline as its arguments.
The default values, though, are taken from here by the argparser-module."""

import os
import dotenv

dotenv.load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
WEBDRIVER_PATH = os.getenv("WEBDRIVER_PATH")
TARGET_DIR_PATH = os.getenv("TARGET_DIR_PATH")
PAGE_TO_SCRAPE = "https://www.reddit.com/top/?t=month"
POSTS_FOR_PARSING_NUM = 500
TOTAL_MAX_WAIT_TIME = 300

HOST = 'localhost'
PORT = 8087
SERVER_NAME = 'reddit-scraper'

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE')
POSTGRES_DB_USER = os.getenv('POSTGRES_DB_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
