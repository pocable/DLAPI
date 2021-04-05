import unittest
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
        self.callback(key, value, DictionaryEventType.SET_EVENT)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.callback(key, self[key], DictionaryEventType.DEL_EVENT)
        super().__delitem__(key)


# Test cases for a dictionary that will callback when a value is changed in it
class TestEventDictionary(unittest.TestCase):
    def test_add_item(self):
        def callback(key, value, event):
            self.assertEqual(event, DictionaryEventType.SET_EVENT)
            self.assertEqual(key, 'test')
            self.assertEqual(value, 'yes')
        edict = EventDictionary(callback)
        edict['test'] = 'yes'

    def test_add_multiple_items(self):
        keys = ['test', 'test2', 'test3']
        values = ['yes', 'no', 'maybe']
        count = 0

        def callback(key, value, event):
            self.assertEqual(event, DictionaryEventType.SET_EVENT)
            self.assertEqual(key, keys[count])
            self.assertEqual(value, values[count])

        edict = EventDictionary(callback)
        for key, value in zip(keys, values):
            edict[key] = value
            count += 1

    def test_update_value(self):
        keys = ['test', 'test2', 'test']
        values = ['yes', 'no', 'maybe']
        count = 0
        
        def callback(key, value, event):
            self.assertEqual(event, DictionaryEventType.SET_EVENT)
            self.assertEqual(key, keys[count])
            self.assertEqual(value, values[count])

        edict = EventDictionary(callback)
        for key, value in zip(keys, values):
            edict[key] = value
            count += 1

        self.assertEqual(len(edict), len(keys) - 1)

    def test_delete_value(self):
        keys = ['te2st', 'te5st', 'test6']
        values = ['yes', 'no', 'maybe']
        count = 0
        
        def callback(key, value, event):
            if count == 3:
                self.assertEqual(event, DictionaryEventType.DEL_EVENT)
                self.assertEqual(key, 'te2st')
                self.assertEqual(value, 'yes')
            else:
                self.assertEqual(event, DictionaryEventType.SET_EVENT)
                self.assertEqual(key, keys[count])
                self.assertEqual(value, values[count])

        edict = EventDictionary(callback)
        for key, value in zip(keys, values):
            edict[key] = value
            count += 1

        del edict[keys[0]]

        self.assertEqual(len(edict), len(keys) - 1)

    def test_delete_multiple(self):
        keys = ['te2st', 'te5st', 'test6']
        values = ['yes', 'no', 'maybe']
        count = 0
        
        def callback(key, value, event):
            if count >= 3:
                self.assertEqual(event, DictionaryEventType.DEL_EVENT)
                if count == 3:
                    self.assertEqual(key, 'te2st')
                    self.assertEqual(value, 'yes')
                if count == 4:
                    self.assertEqual(key, 'te5st')
                    self.assertEqual(value, 'no')
            else:
                self.assertEqual(event, DictionaryEventType.SET_EVENT)
                self.assertEqual(key, keys[count])
                self.assertEqual(value, values[count])

        edict = EventDictionary(callback)
        for key, value in zip(keys, values):
            edict[key] = value
            count += 1

        del edict[keys[0]]
        count += 2
        del edict[keys[1]]

        self.assertEqual(len(edict), len(keys) - 2)

    def test_dictionary_update(self):
        edict = EventDictionary(None)
        tomerge = {'item': 'value', 'item2': 'value2'}
        edict.update(tomerge)
        self.assertEqual(edict, tomerge)


if __name__ == "__main__":
    unittest.main()