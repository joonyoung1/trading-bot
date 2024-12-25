import requests


class Telegram:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token: str = token
        self.chat_id: str = chat_id

        self.base_url = f"https://api.telegram.org/bot{token}/{{method_name}}"

    def send_message(self, message: str) -> None:
        url = self.base_url.format(method_name="sendMessage")
        data = {
            "chat_id": self.chat_id,
            "text": message,
        }
        requests.post(url, data)

    def send_photo(self, file_path: str) -> None:
        url = self.base_url.format(method_name="sendPhoto")
        data = {"chat_id": self.chat_id}

        with open(file_path, "rb") as file:
            files = {"photo": file}
            requests.post(url, data, files=files)
