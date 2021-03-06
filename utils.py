"""Perform operations with strings.

The module helps filter out invalid elements and perform operations with strings
out of parsed data in the parser-module, as well as dict to string and backwards modifications
to allow json-modification and data-validation in the webserver-module."""

import re
from datetime import date
from typing import Optional, List, Tuple, Union, Any
from typing import Dict
from uuid import UUID

from bs4 import BeautifulSoup

pattern_keys = ['unique_id', 'post_url', 'user_name', 'comment_karma', 'post_karma', 'total_karma',
                'user_cakeday', 'post_date', 'comments_number', 'votes_number', 'post_category']


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


def inline_values_to_dict(line: str) -> Dict:
    values = line.strip().split(';')
    return dict(zip(pattern_keys, values))


def info_is_valid(decoded_request_body: Union[Dict[str, str], Any], unique_id: str) -> bool:
    if not isinstance(decoded_request_body, Dict):
        return False

    try:
        id_from_body = UUID(decoded_request_body.get("unique_id", ""))
    except (ValueError, TypeError):
        return False

    if id_from_body != UUID(unique_id):
        return False

    received_keys = decoded_request_body.keys()
    if len(received_keys) <= len(pattern_keys):
        return all(key in pattern_keys for key in received_keys)

    return False


def dict_to_values_inline(decoded_request_body: Dict[str, str]) -> str:
    return ';'.join(
        decoded_request_body[pattern_key] if pattern_key in decoded_request_body.keys()
        else '[DELETED]'
        for pattern_key in pattern_keys
    ) + '\n'


def info_from_sql_db_to_dict(info: Tuple[Union[str, date]]) -> Dict:
    return dict(zip(pattern_keys, list(map(str, info))))


def form_headers(response_body: bytes) -> List[tuple]:
    return [('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', len(response_body))]
