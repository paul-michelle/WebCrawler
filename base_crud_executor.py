from abc import ABC, abstractmethod
from typing import Optional, Union, Any, Dict, List


class BaseCrudExecutor(ABC):
    @abstractmethod
    def insert(self) -> str:
        pass

    @abstractmethod
    def insert_all_remaining(self) -> None:
        pass

    @abstractmethod
    def replace(self) -> Optional[bool]:
        pass

    @abstractmethod
    def delete(self) -> Optional[bool]:
        pass

    @abstractmethod
    def find(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        pass
