import logging
import time
from abc import ABC, abstractmethod
import dotenv
import os
import re
import uuid
from typing import Union, List
from datetime import datetime, date, timedelta
from time import sleep
import bs4
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions \
    import UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.chrome.options import Options
import asyncio
from aiohttp import ClientSession

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
                logging.info(f'Loading of dynamic content finished --- {datetime.now()}.'
                             f'Collected data on {len(posts)} for {time_spent} seconds.')
                break
            if time_spent > MAX_WAIT_TIME:
                logging.warning(f'Max waiting time exceeded. Collected data on {len(posts)} '
                                f'for {MAX_WAIT_TIME} seconds.')
                break

        self.driver.quit()
        return posts


class Scraper:

    def __init__(self, post):
        self.post = post

    async def get_unique_id(self) -> str:
        return uuid.uuid1().hex

    async def get_post_url(self) -> str:
        return self.post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"})['href']

    async def get_post_date(self) -> str:
        published_days_ago = int(self.post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}).contents[0].split()[0])
        post_date = date.today() - timedelta(days=published_days_ago)
        return str(post_date)

    async def get_user_name(self) -> str:
        return self.post.find('a', attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"}).contents[0].split("/")[1]

    async def get_comments_number(self) -> str:
        comments_num_span = self.post.find("span", attrs={"class": "FHCV02u6Cp2zYL0fhQPsO"})
        comments_num_nested_span = comments_num_span.find("span", attrs={"class": "D6SuXeSnAAagG8dKAb4O4"})
        if not comments_num_nested_span:
            return comments_num_span.contents[0].split()[0]
        return comments_num_nested_span.contents[0]

    async def get_votes_number(self) -> str:
        return self.post.find('div', attrs={"class": "_1rZYMD_4xY3gRcSS3p8ODO"}).contents[0]

    async def get_post_category(self) -> str:
        return self.post.find('div', attrs={"class": "_2mHuuvyV9doV3zwbZPtIPG"}).contents[0].contents[0].split("/")[1]

    async def __get_user_profile_soup(self) -> bs4.BeautifulSoup:
        user_url = f'https://www.reddit.com{self.post.find("a", attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"})["href"]}'
        async with ClientSession(headers=HEADERS) as session:
            user_response = await session.request(method="GET", url=user_url)
            html = await user_response.read()
        return BeautifulSoup(html, features='lxml')

    async def __get_user_profile_card(self) -> str:
        user_profile = await self.__get_user_profile_soup()
        return user_profile.find("span", attrs={"id": "profile--id-card--highlight-tooltip--cakeday"})

    async def get_user_cakeday(self) -> Union[str, None]:
        card_available = await self.__get_user_profile_card()
        if card_available:
            return card_available.contents[0]
        logging.warning(f'Failed to reach page https://www.reddit.com'
                            f'{self.post.find("a", attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"})["href"]}')

    async def __get_user_karma_section(self) -> str:
        user_profile = await self.__get_user_profile_soup()
        return user_profile.find("script", attrs={"id": "data"})

    async def get_user_post_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        post_karma_match = re.search('"fromPosts":[\d]*', str(karma_section_block))
        if post_karma_match:
            return post_karma_match.group().split(':')[1]

    async def get_user_comment_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        comment_karma_match = re.search('"fromComments":[\d]*', str(karma_section_block))
        if comment_karma_match:
            return comment_karma_match.group().split(':')[1]

    async def get_user_total_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        total_karma_match = re.search('"total":[\d]*', str(karma_section_block))
        if total_karma_match:
            return total_karma_match.group().split(':')[1]

    async def get_all_info(self) -> Union[str, None]:

        unique_id = self.get_unique_id()
        post_url = self.get_post_url()
        user_name = self.get_user_name()
        comment_karma = self.get_user_comment_karma()
        post_karma = self.get_user_post_karma()
        total_karma = self.get_user_total_karma()
        user_cakeday = self.get_user_cakeday()
        post_date = self.get_post_date()
        comments_number = self.get_comments_number()
        votes_number = self.get_votes_number()
        post_category = self.get_post_category()

        all_info_tuple = await asyncio.gather(unique_id, post_url, user_name, comment_karma, post_karma, total_karma,
                                              user_cakeday, post_date, comments_number, votes_number, post_category)

        if all(all_info_tuple):
            return ';'.join(all_info_tuple)


class ValidDataCollector:

    def __init__(self):
        self.__valid_data = []

    def collect(self, data) -> None:
        if data is not None:
            self.__valid_data.append(data)

    @property
    def data_length(self) -> int:
        return len(self.__valid_data)

    @property
    def data(self) -> List:
        return self.__valid_data


class Saver(ABC):
    @abstractmethod
    def save(self) -> None:
        pass


class TextFileSaver(Saver):

    def __init__(self):
        self.__data = None

    def set_data(self, data) -> None:
        self.__data = data

    @staticmethod
    def remove_old_file() -> None:
        old_file = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(TARGET_DIR_PATH)))
        if old_file:
            logging.info(f'Deleting previous file {old_file.group()} --- {datetime.now()}')
            os.remove(old_file.group())

    @staticmethod
    def calculate_filename() -> str:
        return f'{TARGET_DIR_PATH}{os.sep}reddit-{datetime.now().strftime("%Y%m%d%H%M")}.txt'

    def save(self) -> None:

        new_filename = self.calculate_filename()
        logging.info(f'Starting to write into file --- {datetime.now()}')
        try:
            with open(new_filename, 'w') as file:
                for item in self.__data:
                    file.write(f"{item}\n")
        except OSError:
            logging.error('Unable to write scraped data into the file')
        logging.info(f'Writing to file completed --- {datetime.now()}')


async def main() -> None:

    loader = Loader()
    collector = ValidDataCollector()
    saver = TextFileSaver()

    posts_to_process = loader.load_posts()
    results = await asyncio.gather(*(Scraper(post).get_all_info() for post in posts_to_process))
    for result in results:
        collector.collect(result)
        if collector.data_length == POSTS_FOR_PARSING_NUM:
            break

    data_to_save = collector.data
    saver.set_data(data_to_save)
    saver.remove_old_file()
    saver.save()


if __name__ == '__main__':
    asyncio.run(main())
