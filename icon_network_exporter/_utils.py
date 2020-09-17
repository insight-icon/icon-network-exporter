from abc import ABC, abstractmethod
from time import time
from icon_network_exporter import config


class PeriodicTask(ABC):
    """
    Utility class which runs _perform() at most every period_seconds.
    """

    def __init__(self, period_seconds):
        self.period_seconds = period_seconds
        self.__last_invocation_time = None

    @abstractmethod
    def _perform(self):
        raise NotImplementedError()

    def run(self):
        now = time()
        if self.__last_invocation_time is not None and self.__last_invocation_time + self.period_seconds > now:
            return
        self.__last_invocation_time = now
        self._perform()


def check(condition, error_msg=None):
    if not condition:
        raise (RuntimeError() if error_msg is None else RuntimeError(error_msg))
