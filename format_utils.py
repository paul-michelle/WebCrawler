from typing import Dict

pattern_keys = ['unique_id', 'post_url', 'user_name', 'comment_karma', 'post_karma', 'total_karma',
                'user_cakeday', 'post_date', 'comments_number', 'votes_number', 'post_category']


def inline_values_to_dict(line: str) -> Dict:
    values = line.strip().split(';')
    return dict(zip(pattern_keys, values))


def info_is_valid(decoded_request_body: dict) -> bool:
    received_keys = decoded_request_body.keys()
    if len(received_keys) <= len(pattern_keys):
        mirror_key_pairs = zip(pattern_keys, received_keys)
        return all(pair[0] == pair[1] for pair in mirror_key_pairs)
    return False


def dict_to_values_inline(decoded_request_body: dict) -> str:
    return ';'.join(decoded_request_body.values()) + '\n'
