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
    help='number of port to listen for webserver'
)
argparser.add_argument(
    '--server',
    type=str,
    default=settings.SERVER_NAME,
    help='name of the webserver running on the given address'
)

argparser.add_argument(
    '--postgres-host',
    type=str,
    default=settings.POSTGRES_HOST,
    help='postgresql server address'
)

argparser.add_argument(
    '--postgres-port',
    type=int,
    default=settings.POSTGRES_PORT,
    help='number of port postgres is listening on'
)

argparser.add_argument(
    '--postgres-db',
    type=str,
    default=settings.POSTGRES_DATABASE,
    help='postgres database name'
)

argparser.add_argument(
    '--postgres-user',
    type=str,
    default=settings.POSTGRES_DB_USER,
    help='postgres database username'
)

argparser.add_argument(
    '--postgres-pass',
    type=str,
    default=settings.POSTGRES_PASSWORD,
    help='postgres database password'
)

argparser.add_argument(
    '--mongo-host',
    type=str,
    default=settings.MONGO_HOST,
    help='mongoDB instance address'
)

argparser.add_argument(
    '--mongo-port',
    type=int,
    default=settings.MONGO_PORT,
    help='number of port mondoDB is listening on'
)

argparser.add_argument(
    '--mongo-db',
    type=str,
    default=settings.MONGO_DB_NAME,
    help='mongoDB database name'
)
