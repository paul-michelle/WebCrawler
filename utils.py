import re
from typing import Optional
from bs4 import BeautifulSoup


def get_link(element: Optional[BeautifulSoup]) -> Optional[str]:
    return element is not None and element['href']


def get_contents(element: Optional[BeautifulSoup]) -> Optional[str]:
    return element is not None and element.contents[0].split()[0]


def get_name(element: Optional[BeautifulSoup]) -> Optional[str]:
    return element is not None and element.contents[0].split("/")[1]


def get_category(element: Optional[BeautifulSoup]) -> Optional[str]:
    return element is not None and element.contents[0].contents[0].split("/")[1]


def get_subcontents(element: Optional[BeautifulSoup]) -> Optional[str]:
    return element is not None and element.contents[0]


def get_match(element: Optional[re.Match]) -> Optional[str]:
    if element is not None:
        return element.group().split(':')[1]
