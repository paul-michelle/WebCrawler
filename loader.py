"""Load the info to the parsed.

The module allows to launch and interact with the webbrowser.
Its main task is to load enough raw into to be further refined
by the parser module."""

import logging
import settings
from typing import List
from selenium import webdriver
from selenium.common.exceptions \
    import UnexpectedAlertPresentException, WebDriverException
from bs4 import BeautifulSoup
from time import time
from datetime import datetime

HEADERS = settings.HEADERS
MAX_WAIT_TIME = 30


class Loader:

    def __init__(self, page_to_scrape: str, webdriver_path: str) -> None:
        self._page_to_scrape = page_to_scrape
        self._webdriver_path = webdriver_path
        self._driver = webdriver.Chrome(self._webdriver_path)
        self._loading_start_index = 0

    def __enter__(self) -> None:
        self._navigate_to_page()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._quit()

    def _navigate_to_page(self) -> None:
        try:
            self._driver.get(self._page_to_scrape)
            logging.info(f"WebDriver's navigating to the {self._page_to_scrape} --- {datetime.now()}")
        except WebDriverException:
            logging.error('---Failed to connect. Check Internet connection and the URL.')

    def load_posts(self, posts_to_load_count: int) -> List[BeautifulSoup]:

        logging.info(f'Loading dynamic content of the webpage {self._page_to_scrape} '
                     f'--- {datetime.now()}')
        start_time = time()

        while True:
            scroll_down = "window.scrollBy(0,3000);"
            try:
                self._driver.execute_script(scroll_down)
            except UnexpectedAlertPresentException:
                logging.error('An unexpected alert has appeared. An unexpected modal'
                              'is probably blocking the webdriver from executing'
                              'the scroll-down command')
            content = self._driver.page_source
            soup = BeautifulSoup(content, features="lxml")

            posts = soup.findAll('div', attrs={"class": "Post"},
                                 limit=self._loading_start_index + posts_to_load_count)[self._loading_start_index:]
            time_spent = time() - start_time
            if len(posts) == posts_to_load_count:
                logging.info(f'Loading of dynamic content finished --- {datetime.now()}.'
                             f'Collected data on {len(posts)} for {time_spent} seconds.')
                break
            if time_spent > MAX_WAIT_TIME:
                logging.warning(f'Max waiting time exceeded. Collected data on {len(posts)} '
                                f'for {MAX_WAIT_TIME} seconds.')
                break

        self._loading_start_index += len(posts)

        return posts

    def _quit(self) -> None:
        self._driver.quit()
