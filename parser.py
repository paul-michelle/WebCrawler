import settings
import utils
import re
import uuid
import logging
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from typing import Union, Optional
from datetime import date, timedelta
from constants import *

HEADERS = settings.HEADERS
TARGET_DIR_PATH = settings.TARGET_DIR_PATH


class Parser:

    def __init__(self, post: BeautifulSoup) -> None:
        self.post = post

    @staticmethod
    async def get_unique_id() -> str:
        return uuid.uuid1().hex

    async def get_post_url(self) -> str:
        return utils.get_link(self.post.find(POST_URL["elem"], attrs=POST_URL["attrs"]))

    async def get_post_date(self) -> str:
        published_days_ago = utils.get_contents(self.post.find(POST_DATE["elem"], attrs=POST_DATE["attrs"]))
        return str(date.today() - timedelta(days=int(published_days_ago)))

    async def get_user_name(self) -> str:
        return utils.get_name(self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))

    async def get_comments_number(self) -> str:
        comments_section = self.post.find(COMMENTS["elem"], attrs=COMMENTS["attrs"])
        comments_subsection_exists = comments_section.find(COMMENTS["elem"], attrs=COMMENTS["sub_attrs"])
        if comments_subsection_exists:
            return utils.get_subcontents(comments_subsection_exists)
        return utils.get_contents(comments_section)

    async def get_votes_number(self) -> str:
        return utils.get_subcontents(self.post.find(VOTES["elem"], attrs=VOTES["attrs"]))

    async def get_post_category(self) -> str:
        return utils.get_category(self.post.find(CATEGORY["elem"], attrs=CATEGORY["attrs"]))

    async def __get_user_profile_soup(self) -> BeautifulSoup:
        user_link_available = utils.get_link(self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))
        if user_link_available:
            user_url = f'https://www.reddit.com{user_link_available}'
            async with ClientSession(headers=HEADERS) as session:
                user_response = await session.request(method="GET", url=user_url)
                html = await user_response.read()
            return BeautifulSoup(html, features='lxml')

    async def __get_user_profile_card(self) -> BeautifulSoup:
        user_profile_available = await self.__get_user_profile_soup()
        if user_profile_available:
            return user_profile_available.find(CAKEDAY["elem"], attrs=CAKEDAY["attrs"])

    async def get_user_cakeday(self) -> Union[str, None]:
        card_available = await self.__get_user_profile_card()
        if card_available:
            return utils.get_subcontents(card_available)
        logging.warning(f'Failed to reach page https://www.reddit.com'
                        f'{utils.get_link(self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))}')

    async def __get_user_karma_section(self) -> str:
        user_profile_available = await self.__get_user_profile_soup()
        if user_profile_available:
            return user_profile_available.find(KARMA["elem"], attrs=KARMA["attrs"])

    async def get_user_post_karma(self) -> Optional[str]:
        karma_section_block = await self.__get_user_karma_section()
        return utils.get_match(re.search(KARMA["post"], str(karma_section_block)))

    async def get_user_comment_karma(self) -> Optional[str]:
        karma_section_block = await self.__get_user_karma_section()
        return utils.get_match(re.search(KARMA["comment"], str(karma_section_block)))

    async def get_user_total_karma(self) -> Optional[str]:
        karma_section_block = await self.__get_user_karma_section()
        return utils.get_match(re.search(KARMA["total"], str(karma_section_block)))

    async def get_all_info(self) -> Union[str, None]:

        unique_id = self.get_unique_id()
        post_url = self.get_post_url()
        user_name = self.get_user_name()
        comment_karma = self.get_user_comment_karma()
        post_karma = self.get_user_post_karma()
        total_karma = self.get_user_total_karma()
        user_cakeday = self.get_user_cakeday()
        post_date = self.get_post_date()
        comments_number = self.get_comments_number()
        votes_number = self.get_votes_number()
        post_category = self.get_post_category()

        all_info_tuple = await asyncio.gather(unique_id, post_url, user_name, comment_karma,
                                              post_karma, total_karma, user_cakeday, post_date,
                                              comments_number, votes_number, post_category)
        if all(all_info_tuple):
            return ';'.join(all_info_tuple)
