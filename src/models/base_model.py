from abc import ABC, abstractmethod

from consts import SolutionStatus
from optimize_dataclass.io_dataclass import OutputData


class BaseModel(ABC):
    def __init__(self, optimize_input_data, optimize_config_data):
        self.data = optimize_input_data
        self.config = optimize_config_data

    @abstractmethod
    def add_variables(self):
        pass

    @abstractmethod
    def add_constraints(self):
        pass

    @abstractmethod
    def add_objectives(self):
        pass

    @abstractmethod
    def optimize(self) -> SolutionStatus:
        pass

    @abstractmethod
    def get_result(self) -> OutputData:
        pass
