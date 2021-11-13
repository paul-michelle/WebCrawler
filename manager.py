"""Order the instructions.

The module helps manage the methods supplied by the main operating modules:
loader -> parser -> collector -> saver & webserver."""

import asyncio
import logging
from typing import List
from loader import Loader
from parser import Parser
from collector import ValidDataCollector
from saver import TextFileSaver
from webserver import HTTPServer


class Manager:

    def __init__(self, loader: Loader, collector: ValidDataCollector, saver: TextFileSaver, server: HTTPServer):
        self._loader = loader
        self._collector = collector
        self._saver = saver
        self._server = server

    def get_posts_to_parse(self) -> List:
        posts_to_load_count = self._collector.posts_for_parsing_num - len(self._collector)
        return self._loader.load_posts(posts_to_load_count)

    @staticmethod
    async def parse_posts(posts_to_parse: List) -> List:
        return await asyncio.gather(*(Parser(post).get_all_info() for post in posts_to_parse))

    def collect_valid_info(self, results: List) -> None:
        for result in results:
            self._collector.collect(result)

    def start_server(self):
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logging.info('Server stopped with KeyBoard')

    async def run(self) -> None:
        with self._loader:
            while not self._collector.is_full:
                posts_to_parse = self.get_posts_to_parse()
                parsing_results = await self.parse_posts(posts_to_parse)
                self.collect_valid_info(parsing_results)
            logging.info(f'Collector is filled with valid parsed data. '
                         f'Collected info on {len(self._collector)}')
        self._saver.remove_old_file()
        self.start_server()
