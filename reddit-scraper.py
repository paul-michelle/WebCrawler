import os
import uuid
from time import sleep
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
load_dotenv()

POSTS_FOR_PARSING_NUM = 100
FAILED_SCRAPE_COEFF = 1,1
SCROLLING_ITERATIONS = 100
SLEEPING_INBETWEEN_SCROLLING = 0.07

# SCROLLING_ITERATIONS = 3
# SLEEPING_INBETWEEN_SCROLLING = 0.07
# POSTS_FOR_PARSING_LIMIT = 5

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(r"C:\Users\Pavel\Desktop\chromedriver.exe")
driver.get('https://www.reddit.com/r/all/top/?t=month')
# ____logging in if necessary_______
# login_button = driver.find_element(By.CLASS_NAME, '_2tU8R9NTqhvBrhoNAXWWcP')
# login_button.click()
# driver.switch_to.frame(driver.find_element(By.TAG_NAME, 'iframe'))
# driver.find_element(By.ID, 'loginUsername').send_keys(os.getenv("REDDIT_LOGIN"))
# driver.find_element(By.ID, 'loginPassword').send_keys(os.getenv("REDDIT_PASSWORD"))
# driver.find_element(By.XPATH, '//button[@type="submit"]').click()

scrollDown = "window.scrollBy(0,3000);"
for i in range(SCROLLING_ITERATIONS):
    sleep(SLEEPING_INBETWEEN_SCROLLING)
    driver.execute_script(scrollDown)
content = driver.page_source
driver.quit()
soup = BeautifulSoup(content, features="lxml")

posts = soup.findAll('div', attrs={"class":"Post"},
                     limit=POSTS_FOR_PARSING_NUM*FAILED_SCRAPE_COEFF)
posts_dict = {}
# while len(posts_dict) != POSTS_FOR_PARSING_NUM:
for index, post in enumerate(posts):
    unique_id = uuid.uuid1().hex
    post_url = post.find('a', attrs={"class": "_3jOxDPIQ0KaOWpzvSQo-1s"})['href']
    username = post.find('a', attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"}).contents[0].split("/")[1]
    comments_num = post.find('span', attrs={"class": "FHCV02u6Cp2zYL0fhQPsO"}).contents[0].split()[0]
    votes_num = post.find('div', attrs={"class": "_1rZYMD_4xY3gRcSS3p8ODO"}).contents[0]
    category = post.find('div', attrs={"class": "_2mHuuvyV9doV3zwbZPtIPG"}).contents[0].contents[0].split("/")[1]

    user_url = f'https://www.reddit.com/{post.find("a", attrs={"class": "_2tbHP6ZydRpjI44J3syuqC"})["href"]}'
    headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0)\
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
               }
    user_response = requests.get(user_url, headers=headers).content
    user_soup = BeautifulSoup(user_response, features='lxml')
    post_karma_span = user_soup.find('span', attrs={"class": "karma"})
    if post_karma_span:
        post_karma = post_karma_span.contents[0]
    else:
        post_karma = 'ignorepost'
        continue
    comment_karma_span = user_soup.find('span', attrs={"class": "comment-karma"})
    comment_karma = comment_karma_span.contents[0]

    posts_dict[index] = [post_url, post_karma, comment_karma]

for key, value in posts_dict.items():
    print(key,value)















