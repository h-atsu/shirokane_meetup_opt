from abc import ABC, abstractmethod


class OptimizerBase(ABC):
    def __init__(self, optimize_input_data):
        self.oid = optimize_input_data

    @abstractmethod
    def add_variables(self):
        pass

    @abstractmethod
    def add_constraints(self):
        pass

    @abstractmethod
    def add_objective(self):
        pass

    @abstractmethod
    def optimize(self):
        pass

    @abstractmethod
    def get_result(self):
        pass
