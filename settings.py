import os
import dotenv


dotenv.load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
WEBDRIVER_PATH = os.getenv("WEBDRIVER_PATH")
TARGET_DIR_PATH = os.getenv("TARGET_DIR_PATH")
PAGE_TO_SCRAPE = "https://www.reddit.com/top/?t=month"
POSTS_FOR_PARSING_NUM = 100
