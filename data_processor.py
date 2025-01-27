from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from broker import Broker
    from tracker import Tracker


class DataProcessor:
    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker
