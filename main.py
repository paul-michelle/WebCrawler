"""Run the program.

Set the argparser to read the commandline optional arguments, tune the logging this
the needed threshold (INFO by default). Instantiate the currently needed operating tools:
loader, parser, collector, saver & webserver. Instantiate a manager that gives all the necessary
instructions via its comprehensive run method."""

import os
import logging
import asyncio
from time import time
from datetime import datetime
from argparser import argparser
from loader import Loader
from collector import ValidDataCollector
from txt_executor import TxtExecutor
from webserver import HTTPServer
from manager import Manager

if __name__ == '__main__':
    args = argparser.parse_args()

    logging.basicConfig(filename=f'{args.target_dir_path}{os.sep}reddit-scraper.log',
                        filemode='w', level=logging.INFO)

    current_loader = Loader(webdriver_path=args.chromedriver_path, page_to_scrape=args.url)
    current_collector = ValidDataCollector(posts_for_parsing_num=args.number)
    current_saver = TxtExecutor(target_dir_path=args.target_dir_path)
    current_server = HTTPServer(host=args.host, port=args.port, server_name=args.server,
                                executor=current_saver, collector=current_collector)

    manager = Manager(loader=current_loader,
                      collector=current_collector,
                      saver=current_saver,
                      server=current_server)

    start_time = datetime.now()
    logging.info(f'Reddit-scraper launched --- {start_time}')

    asyncio.run(manager.run())

    logging.info(f'Program completed --- {datetime.now()}. '
                 f'Duration: {time() - start_time.timestamp()} seconds.')
