import settings
from typing import List

POSTS_FOR_PARSING_NUM = settings.POSTS_FOR_PARSING_NUM


class ValidDataCollector:

    def __init__(self):
        self.__valid_data = []

    def collect(self, data) -> None:
        if data is not None and data not in self.__valid_data:
            self.__valid_data.append(data)

    @property
    def data_length(self) -> int:
        return len(self.__valid_data)

    @property
    def data(self) -> List:
        return self.__valid_data

    @property
    def collector_filled(self):
        return self.data_length == POSTS_FOR_PARSING_NUM
