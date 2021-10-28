import os
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import dotenv

dotenv.load_dotenv()

PAGE_TO_SCRAPE = "https://www.reddit.com/top/?t=month"
REDDIT_LOGIN = os.getenv("REDDIT_LOGIN")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
WEBDRIVER_PATH = os.getenv("WEBDRIVER_PATH")

class RedditTest(unittest.TestCase):

    def test_login_button_is_correct(self):
        self.driver = webdriver.Chrome(WEBDRIVER_PATH)
        self.driver.get(PAGE_TO_SCRAPE)

        login_button = self.driver.find_element(By.CLASS_NAME, '_2tU8R9NTqhvBrhoNAXWWcP')
        self.assertTrue('Log' in login_button.text)

        login_button.click()

        self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, 'iframe'))

        loginbox = self.driver.find_element(By.ID, 'loginUsername')
        self.assertTrue('Username' in loginbox.get_attribute('placeholder'))
        loginbox.send_keys(REDDIT_LOGIN)

        passwordbox = self.driver.find_element(By.ID, 'loginPassword')
        self.assertTrue('Password' in passwordbox.get_attribute('placeholder'))
        passwordbox.send_keys(REDDIT_PASSWORD)

        submit_button = self.driver.find_element(By.TAG_NAME, 'button')
        self.assertTrue('Log In' in submit_button.text)
        submit_button.click()



