"""Collect and keep temporarily parsed data.

The module allows to append to a list, checking for duplicates, and keep parsed data
to be later on manipulated via webserver with corresponding executor tools."""

from typing import List


class ValidDataCollector:

    def __init__(self, posts_for_parsing_num) -> None:
        self.posts_for_parsing_num = posts_for_parsing_num
        self.__valid_data = []

    def __len__(self) -> int:
        return len(self.__valid_data)

    def collect(self, data: str) -> None:
        if data is not None and data not in self.__valid_data:
            self.__valid_data.append(data)

    def get_one_entry(self) -> str:
        return self.__valid_data.pop(0)

    def clear(self) -> None:
        self.__valid_data.clear()

    @property
    def data(self) -> List[str]:
        return self.__valid_data

    @property
    def is_full(self) -> bool:
        return len(self) == self.posts_for_parsing_num

    @property
    def is_empty(self) -> bool:
        return len(self) == 0
