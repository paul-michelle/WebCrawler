import settings
from loader import Loader
from collector import ValidDataCollector
from saver import TextFileSaver
from manager import Manager
import asyncio

TARGET_DIR_PATH = settings.TARGET_DIR_PATH
POSTS_FOR_PARSING_NUM = settings.POSTS_FOR_PARSING_NUM

if __name__ == '__main__':

    current_loader = Loader()
    current_collector = ValidDataCollector()
    current_saver = TextFileSaver()

    manager = Manager(loader=current_loader,
                      collector=current_collector,
                      saver=current_saver)

    asyncio.run(manager.run())
