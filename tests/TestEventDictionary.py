from dlapi.utilclasses import EventDictionary, DictionaryEventType
import unittest

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