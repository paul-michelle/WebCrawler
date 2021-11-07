import asyncio
import logging
from typing import List
from parser import Parser
from loader import Loader
from collector import ValidDataCollector
from saver import TextFileSaver
from webserver import HTTPServer


class Manager:

    def __init__(self, loader: Loader, collector: ValidDataCollector, saver: TextFileSaver, server: HTTPServer):
        self.__loader = loader
        self.__collector = collector
        self.__saver = saver
        self.__server = server

    def get_posts_to_parse(self) -> List:
        posts_to_load_count = self.__collector.posts_for_parsing_num - self.__collector.data_length
        return self.__loader.load_posts(posts_to_load_count)

    @staticmethod
    async def parse_posts(posts_to_parse: List) -> List:
        return await asyncio.gather(*(Parser(post).get_all_info() for post in posts_to_parse))

    def collect_valid_info(self, results: List) -> None:
        for result in results:
            self.__collector.collect(result)

    def start_server(self):
        try:
            self.__server.serve_forever()
        except KeyboardInterrupt:
            logging.info('Server stopped with KeyBoard')

    async def run(self) -> None:
        with self.__loader:
            while not self.__collector.is_full:
                posts_to_parse = self.get_posts_to_parse()
                parsing_results = await self.parse_posts(posts_to_parse)
                self.collect_valid_info(parsing_results)
        self.__saver.remove_old_file()
        self.start_server()
