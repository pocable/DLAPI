from enum import Enum

# Class representing a user session. Just a struct.
class Session():
    def __init__(self, ip, token, expiry):
        self._ip = ip
        self._token = token
        self._expiry = expiry

    def get_ip(self):
        return self._ip

    def get_token(self):
        return self._token

    def get_expiry(self):
        return self._expiry

# Update event type used in the EventDictionary callback
class DictionaryEventType(Enum):
    SET_EVENT = 1
    DEL_EVENT = 2

# Dictionary class with a callback to report when an item is changed
class EventDictionary(dict):

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.callback(key, value, DictionaryEventType.SET_EVENT)

    def __delitem__(self, key):
        value = self[key]
        super().__delitem__(key)
        self.callback(key, value, DictionaryEventType.DEL_EVENT)