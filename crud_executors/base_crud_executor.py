"""Absctract Base Class for all executors.

Ensure all the CRUD methods are properly implemented.
All the existing executors and those to be optionally added
in future should subclass from BaseCrudExecutor.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, Any, Dict, List


class BaseCrudExecutor(ABC):

    @abstractmethod
    def insert(self, collected_data: Union[str, List[str]]) -> Union[str, List[str]]:
        pass

    @abstractmethod
    def find(self, unique_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        pass

    @abstractmethod
    def update(self, data: Dict[str, str], unique_id: str) -> Optional[bool]:
        pass

    @abstractmethod
    def delete(self, unique_id: str) -> Optional[bool]:
        pass
