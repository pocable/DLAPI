from enum import Enum
from datetime import date
from collections.abc import Callable

class Session():
    """
    Representation of a user session. This is more of a struct
    Attributes:
        _ip: The IP of the session
        _token: The token provided by the SessionManager
        _expiry: the expiry date of the token
    """

    def __init__(self, ip: str, token: str, expiry: date):
        self._ip = ip
        self._token = token
        self._expiry = expiry

    def get_ip(self) -> str:
        return self._ip

    def get_token(self) -> str:
        return self._token

    def get_expiry(self) -> date:
        return self._expiry

class DictionaryEventType(Enum):
    """
    Event Enum to describe the event returned from an EventDictionary
    """

    SET_EVENT = 1
    DEL_EVENT = 2

class EventDictionary(dict):
    """
    Dictionary class that will callback when items are set or deleted.
    Attributes:
        callback: A call back function of the form func(key, val, DictionaryEventType)
    """
    def __init__(self, callback: Callable[[str, str, DictionaryEventType], None]):
        super().__init__()
        self.callback = callback

    def __setitem__(self, key: str, value: str):
        super().__setitem__(key, value)
        self.callback(key, value, DictionaryEventType.SET_EVENT)

    def __delitem__(self, key: str):
        value = self[key]
        super().__delitem__(key)
        self.callback(key, value, DictionaryEventType.DEL_EVENT)