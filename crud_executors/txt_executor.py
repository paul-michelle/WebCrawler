"""Executor of CRUD operations upon to a txt instance.

The module gives methods to check if a previous output txt-file exists and
remove this file (when being instantiated), as well as to touch a new file
and perform CRUD upon it."""

import logging
import os
import re
import utils
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from .base_crud_executor import BaseCrudExecutor


class TxtInstanceManager:

    def __init__(self, target_dir_path: str) -> None:
        self.__target_dir_path = target_dir_path
        self._remove_old_file()

    def _remove_old_file(self) -> None:
        old_file_exists = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(self.__target_dir_path)))
        if old_file_exists:
            old_file_name = old_file_exists.group()
            logging.info(f'Previous txt-file {old_file_name} is being purged.')
            os.remove(f'{self.__target_dir_path}{os.sep}{old_file_name}')
            return
        logging.info(f'Previous txt-file was never detected.')

    def calculate_filename(self) -> str:
        logging.info(f'New txt-file is being created --- {datetime.now()}')
        return f'{self.__target_dir_path}{os.sep}reddit-{datetime.now().strftime("%Y%m%d%H%M")}.txt'

    @property
    def filename_calculated(self) -> re.Match:
        return re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(self.__target_dir_path)))

    @property
    def path_to_new_file(self) -> str:
        return f'{self.__target_dir_path}{os.sep}{self.filename_calculated.group()}'


class TxtExecutor(BaseCrudExecutor, TxtInstanceManager):

    def __init__(self, target_dir_path: str) -> None:
        super().__init__(target_dir_path)

    def insert(self, post) -> str:
        unique_id = post.split(';')[0]
        if self.filename_calculated:
            with open(self.path_to_new_file, 'a') as f:
                f.write(post + '\n')
                return unique_id
        with open(self.calculate_filename(), 'w') as f:
            f.write(post + '\n')
            return unique_id

    def find(self, unique_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        with open(self.path_to_new_file, 'r') as f:
            already_written_lines = f.readlines()
        if unique_id is None:
            return [utils.inline_values_to_dict(line) for line in already_written_lines]
        for line in already_written_lines:
            if line.startswith(unique_id):
                return utils.inline_values_to_dict(line)

    def update(self, data: Dict[str, Any], unique_id: str) -> Optional[bool]:
        update_performed = False
        with open(self.path_to_new_file, 'r+') as f:
            already_written_lines = f.readlines()
            f.seek(0)
            for line in already_written_lines:
                if line.startswith(unique_id):
                    line = utils.dict_to_values_inline(data)
                    update_performed = True
                f.write(line)
            f.truncate()
        return update_performed

    def delete(self, unique_id: str) -> Optional[bool]:
        deletion_performed = False
        with open(self.path_to_new_file, 'r+') as f:
            already_written_lines = f.readlines()
            f.seek(0)
            for line in already_written_lines:
                if not line.startswith(unique_id):
                    f.write(line)
            f.truncate()
            f.seek(0)
            if len(f.readlines()) != len(already_written_lines):
                deletion_performed = True
        return deletion_performed

    def insert_all_remaining(self, posts: List[str]) -> None:
        pass
