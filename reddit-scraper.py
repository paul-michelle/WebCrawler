import logging
import time
import dotenv
import os
import re
import uuid
from typing import Dict
import requests
from datetime import datetime, date, timedelta
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions \
    import UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

dotenv.load_dotenv()

PAGE_TO_SCRAPE = "https://www.reddit.com/top/?t=month"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
WEBDRIVER_PATH = r"C:\Users\Pavel\Desktop\chromedriver.exe"
TARGET_DIR_PATH = r"\\wsl$\Ubuntu-20.04\home\pavel\itechart\reddit-task"
POSTS_FOR_PARSING_NUM = 100
FAILED_SCRAPE_COEFF = 1.5
SLEEPING_INBETWEEN_SCROLLING = 0.5
MAX_WAIT_TIME = 60

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1080")


def scrape_data(webdriver_path: str = WEBDRIVER_PATH,
                reddit_url: str = PAGE_TO_SCRAPE,
                reddit_login: str = os.getenv("REDDIT_LOGIN"),
                reddit_password: str = os.getenv("REDDIT_PASSWORD"),
                posts_to_parse: int = POSTS_FOR_PARSING_NUM,
                target_dir_path: str = TARGET_DIR_PATH
                ) -> None:

    logging.basicConfig(filename=f'{target_dir_path}{os.sep}reddit-scraper.log', filemode='w', level=logging.INFO)

    # ____opening the webdriver and navigating to page _______
    driver = webdriver.Chrome(webdriver_path)
    try:
        driver.get(reddit_url)
        logging.info(f'WebDriver\'s navigating to the {reddit_url} '
                     f'--- {datetime.now()}')
    except WebDriverException:
        logging.error('---Failed to connect. Check Internet connection and the URL.')

    # ____logging in____
    login_button = driver.find_element(By.CLASS_NAME, '_2tU8R9NTqhvBrhoNAXWWcP')
    login_button.click()
    driver.switch_to.frame(driver.find_element(By.TAG_NAME, 'iframe'))
    driver.find_element(By.ID, 'loginUsername').send_keys(reddit_login)
    driver.find_element(By.ID, 'loginPassword').send_keys(reddit_password)
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()

    #____loading dynamic content within the given MAX_WAIT_TIME____
    logging.info(f'Loading dynamic content of the webpage {PAGE_TO_SCRAPE} '
                 f'--- {datetime.now()}')
    start_time = time.time()
    while True:
        scroll_down = "window.scrollBy(0,3000);"

        try:
            sleep(SLEEPING_INBETWEEN_SCROLLING)
            driver.execute_script(scroll_down)
        except UnexpectedAlertPresentException:
            logging.error('An unexpected alert has appeared. An unexpected modal'
                          'is probably blocking the webdriver from executing'
                          'the scroll-down command')
        content = driver.page_source
        soup = BeautifulSoup(content, features="lxml")
        posts = soup.findAll('div', attrs={"class": "Post"})
        time_spent = time.time() - start_time
        if len(posts) == posts_to_parse * FAILED_SCRAPE_COEFF:
            break
        if time_spent > MAX_WAIT_TIME:
            logging.warning(f'Max waiting time exceeded. Collected data on {len(posts)}')
            break
    logging.info(f'Loading of dynamic content finished --- {datetime.now()}')
    driver.quit()

    #____Collecting the necessary items from the soup____
    logging.info(f'Starting to scrape content --- {datetime.now()}')
    posts_dict: Dict[int, str] = {}
    for index, post in enumerate(posts):

        unique_id = uuid.uuid1().hex
        post_url = post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"})['href']
        post_date = str(date.today() - timedelta(days=
                    int(post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}).contents[0].split()[0])))
        username = post.find('a', attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"}).contents[0].split("/")[1]

        comments_num_span = post.find('span', attrs={"class": "FHCV02u6Cp2zYL0fhQPsO"})
        if comments_num_span.find('span', attrs={"class": "D6SuXeSnAAagG8dKAb4O4"}):
            comments_num = comments_num_span.find('span', attrs={"class": "D6SuXeSnAAagG8dKAb4O4"}).contents[0]
        else:
            comments_num = comments_num_span.contents[0].split()[0]


        votes_num = post.find('div', attrs={"class": "_1rZYMD_4xY3gRcSS3p8ODO"}).contents[0]
        category = post.find('div', attrs={"class": "_2mHuuvyV9doV3zwbZPtIPG"}).contents[0].contents[0].split("/")[1]

        user_url = f'https://www.reddit.com{post.find("a", attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"})["href"]}'
        user_response = requests.get(user_url, headers=HEADERS).content
        user_soup = BeautifulSoup(user_response, features='lxml')
        user_profile_card = user_soup.find("span", attrs={"id": "profile--id-card--highlight-tooltip--cakeday"})
        #____Checking if user personal page is available and does not need age confirmation____
        if user_profile_card:
            user_cakeday = user_profile_card.contents[0]
        else:
            logging.warning(f'Failed to reach user\'s {username} page, hence ignoring the post #{index + 1}')
            continue
        karma_section = user_soup.find("script", attrs={"id": "data"})
        comment_karma = re.search('"fromComments":[\d]*', str(karma_section)).group().split(':')[1]
        post_karma = re.search('"fromPosts":[\d]*', str(karma_section)).group().split(':')[1]
        user_karma = re.search('"total":[\d]*', str(karma_section)).group().split(':')[1]
        #____Writing the data into a dictionary with the given number of posts limitation____
        posts_dict[index] = ';'.join([unique_id, post_url, username, user_karma, user_cakeday, post_karma,
                                comment_karma, post_date, comments_num, votes_num, category])
        if len(posts_dict) == POSTS_FOR_PARSING_NUM:
            break
    logging.info(f'Scraping finished. Collected valid data on {len(posts_dict)}'
                 f' posts --- {datetime.now()}')

    #____Recreating the txt-file according to the 'reddit-YYYYMMDDHHMM.txt format____
    old_file = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(target_dir_path)))
    if old_file:
        os.remove(old_file.group())
    new_file = f'{target_dir_path}{os.sep}reddit-{datetime.now().strftime("%Y%m%d%H%M")}.txt'

    #____Writing the collected data into newly created txt-file____
    logging.info(f'Starting to write info file {new_file} --- {datetime.now()}')
    try:
        with open(new_file, 'w') as file:
            for value in posts_dict.values():
                file.write(f"{value}\n")
    except OSError:
        logging.error('Unable to write scraped data into the file')
    logging.info(f'Writing completed --- {datetime.now()}')

    return None

if __name__ == '__main__':
    scrape_data()



