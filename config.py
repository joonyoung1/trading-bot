import json
from typing import Any


class Config:
    def __init__(self, file_path: str = "./config.json") -> None:
        self.file_path = file_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        with open(self.file_path, "r") as file:
            return json.load(file)

    def save_config(self) -> None:
        with open(self.file_path, "w") as file:
            json.dump(self.config, file, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()


config = Config()
