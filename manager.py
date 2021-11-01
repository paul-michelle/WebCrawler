import settings
from parser import Parser
import asyncio

TARGET_DIR_PATH = settings.TARGET_DIR_PATH
POSTS_FOR_PARSING_NUM = settings.POSTS_FOR_PARSING_NUM


class Manager:

    def __init__(self, loader, collector, saver):
        self.__loader = loader
        self.__collector = collector
        self.__saver = saver

    def get_posts_to_parse(self):
        posts_to_load_count = POSTS_FOR_PARSING_NUM - self.__collector.data_length
        return self.__loader.load_posts(posts_to_load_count)

    @staticmethod
    async def parse_posts(posts_to_parse):
        return await asyncio.gather(*(Parser(post).get_all_info() for post in posts_to_parse))

    def collect_valid_info(self, results):
        for result in results:
            self.__collector.collect(result)

    def save_data(self):
        data_to_save = self.__collector.data
        self.__saver.set_data(data_to_save)
        self.__saver.save()

    async def run(self):
        with self.__loader:
            while not self.__collector.collector_filled:
                posts_to_parse = self.get_posts_to_parse()
                parsing_results = await self.parse_posts(posts_to_parse)
                self.collect_valid_info(parsing_results)
        self.__saver.remove_old_file()
        self.save_data()
