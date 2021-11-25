"""Parse loaded data, filtering out entries with missing info."""

import logging
import settings
import utils
import re
import uuid
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from typing import Union, Optional, Tuple
from datetime import date, timedelta
from constants import *

HEADERS = settings.HEADERS
TARGET_DIR_PATH = settings.TARGET_DIR_PATH


class Parser:

    def __init__(self, post: BeautifulSoup) -> None:
        self._post = post

    @staticmethod
    async def get_unique_id() -> str:
        return uuid.uuid1().hex

    async def get_post_url(self) -> str:
        return utils.get_link(self._post.find(POST_URL["elem"], attrs=POST_URL["attrs"]))

    async def get_post_date(self) -> str:
        published_days_ago = utils.get_contents(self._post.find(POST_DATE["elem"], attrs=POST_DATE["attrs"]))
        return str(date.today() - timedelta(days=int(published_days_ago)))

    async def get_user_name(self) -> str:
        return utils.get_name(self._post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))

    async def get_comments_number(self) -> str:
        comments_section = self._post.find(COMMENTS["elem"], attrs=COMMENTS["attrs"])
        comments_subsection_exists = comments_section.find(COMMENTS["elem"], attrs=COMMENTS["sub_attrs"])
        if comments_subsection_exists:
            return utils.get_subcontents(comments_subsection_exists)
        return utils.get_contents(comments_section)

    async def get_votes_number(self) -> str:
        return utils.get_subcontents(self._post.find(VOTES["elem"], attrs=VOTES["attrs"]))

    async def get_post_category(self) -> str:
        return utils.get_category(self._post.find(CATEGORY["elem"], attrs=CATEGORY["attrs"]))

    async def __get_user_profile_soup(self) -> BeautifulSoup:
        user_link_available = utils.get_link(self._post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))
        if user_link_available:
            user_url = f'https://www.reddit.com{user_link_available}'
            async with ClientSession(headers=HEADERS, trust_env=True) as session:
                user_response = await session.request(method="GET", url=user_url)
                html = await user_response.read()
            return BeautifulSoup(html, features='lxml')

    async def get_user_details(self) -> Optional[Tuple[str]]:
        user_profile_available = await self.__get_user_profile_soup()
        if user_profile_available:
            card_available = user_profile_available.find(CAKEDAY["elem"], attrs=CAKEDAY["attrs"])
            if not card_available:
                logging.warning(f'Failed to reach page https://www.reddit.com'
                                f'{utils.get_link(self._post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]))}')
                return
            user_cakeday = utils.get_subcontents(card_available)
            karma_section_block = user_profile_available.find(KARMA["elem"], attrs=KARMA["attrs"])
            post_karma = utils.get_match(re.search(KARMA["post"], str(karma_section_block)))
            comment_karma = utils.get_match(re.search(KARMA["comment"], str(karma_section_block)))
            total_karma = utils.get_match(re.search(KARMA["total"], str(karma_section_block)))
            if all([post_karma, comment_karma, total_karma]):
                return post_karma, comment_karma, total_karma, user_cakeday

    async def get_all_info(self) -> Union[str, None]:

        unique_id = self.get_unique_id()
        post_url = self.get_post_url()
        user_name = self.get_user_name()
        user_details = self.get_user_details()
        post_date = self.get_post_date()
        comments_number = self.get_comments_number()
        votes_number = self.get_votes_number()
        post_category = self.get_post_category()

        collected_info = await asyncio.gather(unique_id, post_url, user_name, user_details,
                                              post_date, comments_number, votes_number, post_category)
        valid_info = []
        for i in collected_info:
            if isinstance(i, str):
                valid_info.append(i)
                continue
            if isinstance(i, tuple):
                valid_info.extend(i)
                continue
            return

        return ';'.join(valid_info)
