import os
import re
import logging
import settings
from datetime import datetime
from abc import ABC, abstractmethod

TARGET_DIR_PATH = settings.TARGET_DIR_PATH
logging.basicConfig(filename=f'{TARGET_DIR_PATH}{os.sep}reddit-scraper.log', filemode='w', level=logging.INFO)


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
