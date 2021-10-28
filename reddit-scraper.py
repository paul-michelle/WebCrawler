import logging
import time
from abc import ABC, abstractmethod
import dotenv
import os
import re
import uuid
from typing import Union, List
import requests
from datetime import datetime, date, timedelta
from time import sleep
import bs4
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions \
    import UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

dotenv.load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}

PAGE_TO_SCRAPE = "https://www.reddit.com/top/?t=month"
REDDIT_LOGIN = os.getenv("REDDIT_LOGIN")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
WEBDRIVER_PATH = os.getenv("WEBDRIVER_PATH")
TARGET_DIR_PATH = os.getenv("TARGET_DIR_PATH")
POSTS_FOR_PARSING_NUM = 100

FAILED_SCRAPE_COEFF = 1.5
SLEEPING_INBETWEEN_SCROLLING = 1
MAX_WAIT_TIME = 60

logging.basicConfig(filename=f'{TARGET_DIR_PATH}{os.sep}reddit-scraper.log', filemode='w', level=logging.INFO)


class Loader:

    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")

    def __init__(self):
        self.driver = webdriver.Chrome(WEBDRIVER_PATH)

    def load_posts(self, posts_to_parse=POSTS_FOR_PARSING_NUM):
        try:
            self.driver.get(PAGE_TO_SCRAPE)
            logging.info(f'WebDriver\'s navigating to the {PAGE_TO_SCRAPE} '
                         f'--- {datetime.now()}')
        except WebDriverException:
            logging.error('---Failed to connect. Check Internet connection and the URL.')

        login_button = self.driver.find_element(By.CLASS_NAME, '_2tU8R9NTqhvBrhoNAXWWcP')
        login_button.click()
        self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, 'iframe'))
        self.driver.find_element(By.ID, 'loginUsername').send_keys(REDDIT_LOGIN)
        self.driver.find_element(By.ID, 'loginPassword').send_keys(REDDIT_PASSWORD)
        # sleep(3)
        submit_button = self.driver.find_element(By.TAG_NAME, 'button')
        submit_button.click()

        logging.info(f'Loading dynamic content of the webpage {PAGE_TO_SCRAPE} '
                     f'--- {datetime.now()}')
        start_time = time.time()
        while True:
            scroll_down = "window.scrollBy(0,3000);"
            try:
                sleep(SLEEPING_INBETWEEN_SCROLLING)
                self.driver.execute_script(scroll_down)
            except UnexpectedAlertPresentException:
                logging.error('An unexpected alert has appeared. An unexpected modal'
                              'is probably blocking the webdriver from executing'
                              'the scroll-down command')
            content = self.driver.page_source
            soup = BeautifulSoup(content, features="lxml")
            posts = soup.findAll('div', attrs={"class": "Post"})
            time_spent = time.time() - start_time
            if len(posts) > posts_to_parse * FAILED_SCRAPE_COEFF:
                break
            if time_spent > MAX_WAIT_TIME:
                logging.warning(f'Max waiting time exceeded. Collected data on {len(posts)}')
                break
        logging.info(f'Loading of dynamic content finished --- {datetime.now()}')
        self.driver.quit()
        return posts


class Scraper:

    def __init__(self, post):
        self.post = post

    def get_unique_id(self) -> str:
        return uuid.uuid1().hex

    def get_post_url(self) -> str:
        return self.post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"})['href']

    def get_post_date(self) -> str:
        published_days_ago = int(self.post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}).contents[0].split()[0])
        post_date = date.today() - timedelta(days=published_days_ago)
        return str(post_date)

    def get_user_name(self) -> str:
        return self.post.find('a', attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"}).contents[0].split("/")[1]

    def get_comments_number(self) -> str:
        comments_num_span = self.post.find("span", attrs={"class": "FHCV02u6Cp2zYL0fhQPsO"})
        comments_num_nested_span = comments_num_span.find("span", attrs={"class": "D6SuXeSnAAagG8dKAb4O4"})
        if not comments_num_nested_span:
            return comments_num_span.contents[0].split()[0]
        return comments_num_nested_span.contents[0]

    def get_votes_number(self) -> str:
        return self.post.find('div', attrs={"class": "_1rZYMD_4xY3gRcSS3p8ODO"}).contents[0]

    def get_post_category(self) -> str:
        return self.post.find('div', attrs={"class": "_2mHuuvyV9doV3zwbZPtIPG"}).contents[0].contents[0].split("/")[1]

    def __get_user_profile_soup(self) -> bs4.BeautifulSoup:
        user_url = f'https://www.reddit.com{self.post.find("a", attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"})["href"]}'
        user_response = requests.get(user_url, headers=HEADERS).content
        return BeautifulSoup(user_response, features='lxml')

    def __get_user_profile_card(self) -> str:
        return self.__get_user_profile_soup().find("span", attrs={"id": "profile--id-card--highlight-tooltip--cakeday"})

    def get_user_cakeday(self) -> Union[str, None]:
        if not self.__get_user_profile_card():
            logging.warning(f'Failed to reach user\'s {self.get_user_name()} page')
            return
        return self.__get_user_profile_card().contents[0]

    def __get_user_karma_section(self) -> str:
        return self.__get_user_profile_soup().find("script", attrs={"id": "data"})

    def get_user_post_karma(self) -> Union[str, None]:
        post_karma_match = re.search('"fromPosts":[\d]*', str(self.__get_user_karma_section()))
        if not post_karma_match:
            return
        return post_karma_match.group().split(':')[1]

    def get_user_comment_karma(self) -> Union[str, None]:
        comment_karma_match = re.search('"fromComments":[\d]*', str(self.__get_user_karma_section()))
        if not comment_karma_match:
            return
        return comment_karma_match.group().split(':')[1]

    def get_user_total_karma(self) -> Union[str, None]:
        total_karma_match = re.search('"total":[\d]*', str(self.__get_user_karma_section()))
        if not total_karma_match:
            return
        return total_karma_match.group().split(':')[1]

    def get_all_info(self) -> Union[str, None]:

        all_info = [self.get_unique_id(),
                    self.get_post_url(),
                    self.get_user_name(),
                    self.get_user_comment_karma(),
                    self.get_user_post_karma(),
                    self.get_user_total_karma(),
                    self.get_user_cakeday(),
                    self.get_post_date(),
                    self.get_comments_number(),
                    self.get_votes_number(),
                    self.get_post_category()]

        if all(all_info):
            return ';'.join(all_info)
        return


class ValidDataCollector:

    valid_data = []

    def collect(self, data) -> None:
        if data is not None:
            self.valid_data.append(data)

    def give_data(self) -> List:
        return self.valid_data


class Saver(ABC):
    @abstractmethod
    def save(self):
        pass


class TextFileSaver(Saver):

    def __init__(self, data):
        self.data = data

    def save(self) -> None:

        old_file = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(TARGET_DIR_PATH)))
        if old_file:
            os.remove(old_file.group())
        new_file = f'{TARGET_DIR_PATH}{os.sep}reddit-{datetime.now().strftime("%Y%m%d%H%M")}.txt'

        logging.info(f'Starting to write into file {new_file} --- {datetime.now()}')
        try:
            with open(new_file, 'w') as file:
                for item in self.data:
                    file.write(f"{item}\n")
        except OSError:
            logging.error('Unable to write scraped data into the file')
        logging.info(f'Writing to file completed --- {datetime.now()}')


def main() -> None:

    loader = Loader()
    collector = ValidDataCollector()

    for post in loader.load_posts():
        scraper = Scraper(post)
        data = scraper.get_all_info()
        collector.collect(data)
        if len(collector.valid_data) == POSTS_FOR_PARSING_NUM:
            logging.info(f'Scraped valid data on {POSTS_FOR_PARSING_NUM} '
                         f'posts --- {datetime.now()}')
            break

    data_to_save = collector.give_data()
    saver = TextFileSaver(data_to_save)
    saver.save()


if __name__ == '__main__':
    main()
