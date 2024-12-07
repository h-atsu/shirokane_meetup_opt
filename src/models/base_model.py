from abc import ABC, abstractmethod
from typing import TypeVar

from consts import SolutionStatus
from optimize_dataclass.io_dataclass import OutputData

T = TypeVar("T")


class BaseModel(ABC):
    def __init__(self, optimize_input_data, optimize_config_data):
        self.data = optimize_input_data
        self.config = optimize_config_data

    @abstractmethod
    def add_variables(self: T) -> T:
        pass

    @abstractmethod
    def add_constraints(self: T) -> T:
        pass

    @abstractmethod
    def add_objectives(self: T) -> T:
        pass

    @abstractmethod
    def optimize(self) -> SolutionStatus:
        pass

    @abstractmethod
    def get_result(self) -> OutputData:
        pass
