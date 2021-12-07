"""Run the program.

Set the argparser to read the commandline optional arguments, tune the logging this
the needed threshold (INFO by default). Instantiate the currently needed operating tools:
loader, parser, collector , executor, and webserver. Instantiate a manager that gives all the necessary
instructions via its comprehensive run method."""

import logging
import os
import asyncio
from time import time
from datetime import datetime
from argparser import argparser
from loader import Loader
from collector import ValidDataCollector
from webserver import HTTPServer
from manager import Manager
from crud_executors import (
    base_crud_executor, sql_executor, nosql_executor, txt_executor
)


class ExecutorType:

    @staticmethod
    def txt(target_dir: str) -> base_crud_executor.BaseCrudExecutor:
        return txt_executor.TxtExecutor(target_dir)

    @staticmethod
    def sql() -> base_crud_executor.BaseCrudExecutor:
        return sql_executor.PostgreSQLExecutor()

    @staticmethod
    def nosql() -> base_crud_executor.BaseCrudExecutor:
        return nosql_executor.MongoExecutor()


if __name__ == '__main__':
    args = argparser.parse_args()
    logging.basicConfig(filename=f'{args.target_dir_path}{os.sep}reddit-scraper.log',
                        filemode='w', level=logging.INFO)

    current_executor = ExecutorType().sql()

    current_loader = Loader(webdriver_path=args.chromedriver_path, page_to_scrape=args.url)
    current_collector = ValidDataCollector(posts_for_parsing_num=args.number)
    current_server = HTTPServer(host=args.host, port=args.port, server_name=args.server,
                                executor=current_executor, collector=current_collector)
    manager = Manager(loader=current_loader, collector=current_collector, server=current_server)

    start_time = datetime.now()
    logging.info(f'Reddit-scraper launched --- {start_time}. CRUD-executor: {current_executor}')

    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logging.info(f'Program terminated --- {datetime.now()}. '
                     f'Duration: {time() - start_time.timestamp()} seconds.')
