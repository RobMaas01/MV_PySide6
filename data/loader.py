"""
Achtergrond-thread voor het laden van DataStore.
"""
from PySide6.QtCore import QThread, Signal
from data.store import DataStore


class DataLoader(QThread):
    finished = Signal(object)   # DataStore-instantie

    def run(self) -> None:
        store = DataStore.load()
        self.finished.emit(store)
