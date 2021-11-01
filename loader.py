import os
import settings
import logging
from selenium import webdriver
from selenium.common.exceptions \
    import UnexpectedAlertPresentException, WebDriverException
from bs4 import BeautifulSoup
import time
from datetime import datetime, date, timedelta


TARGET_DIR_PATH = settings.TARGET_DIR_PATH
HEADERS = settings.HEADERS
PAGE_TO_SCRAPE = settings.PAGE_TO_SCRAPE
WEBDRIVER_PATH = settings.WEBDRIVER_PATH
POSTS_FOR_PARSING_NUM = settings.POSTS_FOR_PARSING_NUM
MAX_WAIT_TIME = 30

logging.basicConfig(filename=f'{TARGET_DIR_PATH}{os.sep}reddit-scraper.log', filemode='w', level=logging.INFO)


class Loader:

    def __init__(self) -> None:
        self.driver = webdriver.Chrome(WEBDRIVER_PATH)
        self.loading_start_index = 0

    def __enter__(self) -> None:
        self.navigate_to_page()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.quit()

    def navigate_to_page(self) -> None:
        try:
            self.driver.get(PAGE_TO_SCRAPE)
            logging.info(f'WebDriver\'s navigating to the {PAGE_TO_SCRAPE} '
                         f'--- {datetime.now()}')
        except WebDriverException:
            logging.error('---Failed to connect. Check Internet connection and the URL.')

    def load_posts(self, posts_to_load_count) -> BeautifulSoup:

        logging.info(f'Loading dynamic content of the webpage {PAGE_TO_SCRAPE} '
                     f'--- {datetime.now()}')
        start_time = time.time()

        while True:
            scroll_down = "window.scrollBy(0,3000);"
            try:
                self.driver.execute_script(scroll_down)
            except UnexpectedAlertPresentException:
                logging.error('An unexpected alert has appeared. An unexpected modal'
                              'is probably blocking the webdriver from executing'
                              'the scroll-down command')
            content = self.driver.page_source
            soup = BeautifulSoup(content, features="lxml")

            posts = soup.findAll('div', attrs={"class": "Post"},
                                 limit=self.loading_start_index + posts_to_load_count)[self.loading_start_index:]
            time_spent = time.time() - start_time
            if len(posts) == posts_to_load_count:
                logging.info(f'Loading of dynamic content finished --- {datetime.now()}.'
                             f'Collected data on {len(posts)} for {time_spent} seconds.')
                break
            if time_spent > MAX_WAIT_TIME:
                logging.warning(f'Max waiting time exceeded. Collected data on {len(posts)} '
                                f'for {MAX_WAIT_TIME} seconds.')
                break

        self.loading_start_index += len(posts)

        return posts

    def quit(self):
        self.driver.quit()
