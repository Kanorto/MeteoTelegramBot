import json
from pathlib import Path
from typing import Dict

from .config import USERS_FILE


class Storage:
    def __init__(self, path: str = USERS_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('{}')

    def load_users(self) -> Dict[str, dict]:
        return json.loads(self.path.read_text())

    def save_users(self, data: Dict[str, dict]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def get_user(self, user_id: int) -> dict:
        users = self.load_users()
        return users.get(str(user_id), {})

    def set_user(self, user_id: int, info: dict) -> None:
        users = self.load_users()
        users[str(user_id)] = info
        self.save_users(users)
