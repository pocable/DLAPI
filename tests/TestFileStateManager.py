import unittest
from dlapi.managers import FileStateManager

def read_state_manager_file():
    z = open("./test_state/state.txt", 'r')
    lines = z.readlines()
    z.close()
    return lines

class TestFileStateManager(unittest.TestCase):
    """
    Test the original State manager class, a class which wraps
    the event dictionary but does it to what we need.
    """
    
    # Test that setting a new value updates the file
    def test_internal_call(self):
        mngr = FileStateManager("./test_state/state.txt")
        mngr['test'] = 'z'
        x = read_state_manager_file()
        self.assertEqual(x, ['{"test": "z"}'])

    # Test that setting multiple values reflect a proper update
    def test_multiple_internal_call(self):
        mngr = FileStateManager("./test_state/state.txt")
        mngr['test'] = 'z'
        mngr['test2'] = 'kkz'
        x = read_state_manager_file()
        self.assertEqual(x, ['{"test": "z", "test2": "kkz"}'])

    def test_removal(self):
        mngr = FileStateManager("./test_state/state.txt")
        mngr['test'] = 'z'
        mngr['test2'] = 'kkz'
        del mngr['test2']
        x = read_state_manager_file()
        self.assertEqual(x, ['{"test": "z"}'])

    def test_clear_set_remove(self):
        mngr = FileStateManager("./test_state/state.txt")
        mngr.save_state()
        self.assertEqual(mngr, {})

        mngr['test'] = 'z'
        mngr['test2'] = 'kkz'
        x = read_state_manager_file()
        self.assertEqual(x, ['{"test": "z", "test2": "kkz"}'])

        del mngr['test']
        x = read_state_manager_file()
        self.assertEqual(x, ['{"test2": "kkz"}'])
        
        clean = FileStateManager("./test_state/state.txt")
        clean.save_state()
        clean.load_state()
        self.assertEqual(clean, {})
