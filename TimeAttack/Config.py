from dataclasses import dataclass
import requests

@dataclass
class Config:
    """
    The configuration object for the code.
    """

    server_ip: str
    username: str
    difficulty: str
    format: str
    retries: int
    password_chars: str
    max_password_length: int
    session: requests.Session

TASK_CONFIG: Config | None = None
