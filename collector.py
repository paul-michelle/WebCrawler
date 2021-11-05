from typing import List


class ValidDataCollector:

    def __init__(self, posts_for_parsing_num) -> None:
        self.posts_for_parsing_num = posts_for_parsing_num
        self.__valid_data = []

    def collect(self, data: str) -> None:
        if data is not None and data not in self.__valid_data:
            self.__valid_data.append(data)

    @property
    def data_length(self) -> int:
        return len(self.__valid_data)

    @property
    def data(self) -> List:
        return self.__valid_data

    @property
    def is_full(self) -> bool:
        return self.data_length == self.posts_for_parsing_num

    @property
    def is_empty(self) -> bool:
        return self.data_length == 0
