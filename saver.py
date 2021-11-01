import os
import re
import logging
from datetime import datetime
from abc import ABC, abstractmethod


class Saver(ABC):
    @abstractmethod
    def save(self) -> None:
        pass


class TextFileSaver(Saver):

    def __init__(self, target_dir_path) -> None:
        self.__target_dir_path = target_dir_path
        self.__data = None

    def set_data(self, data) -> None:
        self.__data = data

    def remove_old_file(self) -> None:
        old_file_exists = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(self.__target_dir_path)))
        if old_file_exists:
            logging.info(f'Deleting previous file named {old_file_exists.group()} --- {datetime.now()}')
            os.remove(f'{self.__target_dir_path}{os.sep}{old_file_exists.group()}')

    def calculate_filename(self) -> str:
        return f'{self.__target_dir_path}{os.sep}reddit-{datetime.now().strftime("%Y%m%d%H%M")}.txt'

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
