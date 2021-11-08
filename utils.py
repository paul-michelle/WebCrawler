import re
from typing import Optional, List
from typing import Dict
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


def info_is_valid(decoded_request_body: Dict[str:str]) -> bool:
    received_keys = decoded_request_body.keys()
    if len(received_keys) <= len(pattern_keys):
        mirror_key_pairs = zip(pattern_keys, received_keys)
        return all(pair[0] == pair[1] for pair in mirror_key_pairs)
    return False


def dict_to_values_inline(decoded_request_body: Dict[str:str]) -> str:
    return ';'.join(decoded_request_body.values()) + '\n'


def form_headers(response_body: bytes) -> List[tuple]:
    return [('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', len(response_body))]
