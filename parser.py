import settings
import re
import uuid
import logging
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from typing import Union
from datetime import date, timedelta
from constants import *

HEADERS = settings.HEADERS
TARGET_DIR_PATH = settings.TARGET_DIR_PATH


class Parser:

    def __init__(self, post) -> None:
        self.post = post

    @staticmethod
    async def get_unique_id() -> str:
        return uuid.uuid1().hex

    async def get_post_url(self) -> str:
        return self.post.find(POST_URL["elem"], attrs=POST_URL["attrs"])['href']

    async def get_post_date(self) -> str:
        published_days_ago = int(self.post.find(POST_DATE["elem"], attrs=POST_DATE["attrs"]).contents[0].split()[0])
        post_date = date.today() - timedelta(days=published_days_ago)
        return str(post_date)

    async def get_user_name(self) -> str:
        return self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"]).contents[0].split("/")[1]

    async def get_comments_number(self) -> str:
        comments_num_span = self.post.find(COMMENTS["elem"], attrs=COMMENTS["attrs"])
        comments_num_nested_span = comments_num_span.find(COMMENTS["elem"], attrs=COMMENTS["nested_attrs"])
        if not comments_num_nested_span:
            return comments_num_span.contents[0].split()[0]
        return comments_num_nested_span.contents[0]

    async def get_votes_number(self) -> str:
        return self.post.find(VOTES["elem"], attrs=VOTES["attrs"]).contents[0]

    async def get_post_category(self) -> str:
        return self.post.find(CATEGORY["elem"], attrs=CATEGORY["attrs"]).contents[0].contents[0].split("/")[1]

    async def __get_user_profile_soup(self) -> BeautifulSoup:
        user_url = f'https://www.reddit.com{self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"])["href"]}'
        async with ClientSession(headers=HEADERS) as session:
            user_response = await session.request(method="GET", url=user_url)
            html = await user_response.read()
        return BeautifulSoup(html, features='lxml')

    async def __get_user_profile_card(self) -> str:
        user_profile = await self.__get_user_profile_soup()
        return user_profile.find(CAKEDAY["elem"], attrs=CAKEDAY["attrs"])

    async def get_user_cakeday(self) -> Union[str, None]:
        card_available = await self.__get_user_profile_card()
        if card_available:
            return card_available.contents[0]
        logging.warning(f'Failed to reach page https://www.reddit.com'
                        f'{self.post.find(USER_NAME["elem"], attrs=USER_NAME["attrs"])["href"]}')

    async def __get_user_karma_section(self) -> str:
        user_profile = await self.__get_user_profile_soup()
        return user_profile.find(KARMA["elem"], attrs=KARMA["attrs"])

    async def get_user_post_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        post_karma_match = re.search(KARMA["post"], str(karma_section_block))
        if post_karma_match:
            return post_karma_match.group().split(':')[1]

    async def get_user_comment_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        comment_karma_match = re.search(KARMA["comment"], str(karma_section_block))
        if comment_karma_match:
            return comment_karma_match.group().split(':')[1]

    async def get_user_total_karma(self) -> Union[str, None]:
        karma_section_block = await self.__get_user_karma_section()
        total_karma_match = re.search(KARMA["total"], str(karma_section_block))
        if total_karma_match:
            return total_karma_match.group().split(':')[1]

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

        all_info_tuple = await asyncio.gather(unique_id, post_url, user_name, comment_karma, post_karma, total_karma,
                                              user_cakeday, post_date, comments_number, votes_number, post_category)

        if all(all_info_tuple):
            return ';'.join(all_info_tuple)
