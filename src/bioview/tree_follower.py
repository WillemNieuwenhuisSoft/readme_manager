from abc import ABC, abstractmethod
from pathlib import Path


class TreeFollowerObserver(ABC):
    @abstractmethod
    def update(self, event: str, item_id: str):
        pass


class Tree:
    def __init__(self):
        self._observers = []

    def attach(self, observer: TreeFollowerObserver):
        self._observers.append(observer)

    def detach(self, observer: TreeFollowerObserver):
        self._observers.remove(observer)

    def notify(self, event: str, path: Path):
        for observer in self._observers:
            observer.update(event, path)
