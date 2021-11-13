"""Allow to optionally set key project constants via commandline."""

import argparse
import settings

argparser = argparse.ArgumentParser()
argparser.add_argument(
    '--chromedriver-path',
    type=str,
    default=settings.WEBDRIVER_PATH,
    help='/path/to/chromedriver. Please note you need NOT put a separator (slash or backslash)'
         ' at the end of the path'
)
argparser.add_argument(
    '--target-dir-path',
    type=str,
    default=settings.TARGET_DIR_PATH,
    help='/path/to/dir to store txt and log files with scraping results. '
         'Please note you need NOT put a separator (slash or backslash) at the end of the path'
)
argparser.add_argument(
    '--url',
    type=str,
    default=settings.PAGE_TO_SCRAPE,
    help='url of the page from which to scrape info'
)
argparser.add_argument(
    '--number',
    type=int,
    default=settings.POSTS_FOR_PARSING_NUM,
    help='number of posts to parse'
)
argparser.add_argument(
    '--host',
    type=str,
    default=settings.HOST,
    help='host address'
)
argparser.add_argument(
    '--port',
    type=int,
    default=settings.PORT,
    help='number of port to launch webserver on'
)
argparser.add_argument(
    '--server',
    type=str,
    default=settings.SERVER_NAME,
    help='name of the webserver running on the given address'
)
