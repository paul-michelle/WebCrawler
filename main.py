import os
import logging
import asyncio
from time import time
from datetime import datetime
from argparser import argparser
from loader import Loader
from collector import ValidDataCollector
from saver import TextFileSaver
from manager import Manager

if __name__ == '__main__':
    args = argparser.parse_args()

    logging.basicConfig(filename=f'{args.target_dir_path}{os.sep}reddit-scraper.log',
                        filemode='w', level=logging.INFO)

    current_loader = Loader(webdriver_path=args.chromedriver_path, page_to_scrape=args.url)
    current_collector = ValidDataCollector(posts_for_parsing_num=args.number)
    current_saver = TextFileSaver(target_dir_path=args.target_dir_path)

    manager = Manager(loader=current_loader,
                      collector=current_collector,
                      saver=current_saver)

    start_time = datetime.now()
    logging.info(f'Reddit-scraper program launched --- {start_time}')

    asyncio.run(manager.run())

    logging.info(f'Reddit-scraping completed --- {datetime.now()}. '
                 f'Execution time: {time() - start_time.timestamp()} seconds.')
