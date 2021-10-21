import os
from dotenv import load_dotenv
load_dotenv()
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By



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

content = driver.page_source
soup = BeautifulSoup(content, features="lxml")

# for i in range(10):
#     scrollDown = "window.scrollBy(0,2000);"
#     driver.execute_script(scrollDown)
#     sleep(1)

anchors = soup.findAll('div', attrs={"class":"Post"}, limit=100)
print(anchors)

driver.quit()

# for post in soup.select('.Post', limit=100):
#     print(post)
    # try:
    #     print(post.select('._3jOxDPIQ0KaOWpzvSQo-1s')[0]['href'])
    # except:
    #     continue







