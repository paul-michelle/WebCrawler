import re
from typing import Optional
from bs4 import BeautifulSoup


def get_link(element: BeautifulSoup) -> str:
    return element['href']


def get_contents(element: BeautifulSoup) -> str:
    return element.contents[0].split()[0]


def get_name(element: BeautifulSoup) -> str:
    return element.contents[0].split("/")[1]


def get_category(element: BeautifulSoup) -> str:
    return element.contents[0].contents[0].split("/")[1]


def get_subcontents(element: BeautifulSoup) -> str:
    return element.contents[0]


def get_match(element: Optional[re.Match]) -> Optional[str]:
    if element is not None:
        return element.group().split(':')[1]
