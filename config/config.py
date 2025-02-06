import os
import json
from typing import Any

from schemas import ConfigKeys


class Config:
    def __init__(self, filepath: str = "config.json") -> None:
        self.filepath = filepath
        self.config = self.load_config()

        if ConfigKeys.PIVOT not in self.config:
            self.set(ConfigKeys.PIVOT, float(os.getenv(ConfigKeys.PIVOT)))

    def load_config(self) -> dict:
        with open(self.filepath, "r") as file:
            return json.load(file)

    def save_config(self) -> None:
        with open(self.filepath, "w") as file:
            json.dump(self.config, file, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()


config = Config()
