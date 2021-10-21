from dlapi.managers import StateManager
import unittest
import os

class TestStateManager(unittest.TestCase):
    """
    Test the new StateManager based off using
    sqlite3 instead of file.
    """

    def setUp(self):
        db = StateManager("test.db")
        db.delete_all()

    def test_connection(self):
        StateManager("test.db")


    def test_get_empty(self):
        db = StateManager("test.db")
        db.clear()
        val = db.get_all()
        self.assertEqual(val, [])

        val = db.get_info('asfas')
        self.assertEqual(val, ())

        val = db.get_all_as_dict()
        self.assertEqual(val, {})

    def test_add_content_duplicate(self):
        db = StateManager("test.db")
        db.add_content('8958h32', '32032h823', 'Test Title')
        db.add_content('8958h32', '32032h823', 'Test Title')
        db.add_content('8958h32', '32032h823', 'Test Title')

    def test_add_content(self):
        db = StateManager("test.db")
        db.add_content('8958h32', '32032h823', 'Test Title')
        db.add_content('t2g2g', '24g2g23w')

        title, path = db.get_info('8958h32')
        self.assertEqual(title, 'Test Title')
        self.assertEqual(path, '32032h823')

        title, path = db.get_info('t2g2g')
        self.assertEqual(title, '')
        self.assertEqual(path, '24g2g23w')

    def test_get_all_ids_and_delete_all(self):
        db = StateManager("test.db")
        db.delete_all()
        db.add_content('25235', 'i325')
        db.add_content('25255', '325')
        db.add_content('25435', '25')

        ids = db.get_all_ids()
        self.assertEqual(ids, ['25235', '25255', '25435'])

        db.delete_all()
        ids = db.get_all_ids()
        self.assertEqual(ids, [])

    def test_delete_one(self):
        db = StateManager("test.db")
        db.delete_all()
        db.add_content('25235', 'i325')
        db.add_content('25255', '325')
        db.add_content('25435', '25')
        db.delete_id('25235')

        ids = db.get_all_ids()
        self.assertEqual(ids, ['25255', '25435'])

    def test_length(self):
        db = StateManager("test.db")
        db.delete_all()
        self.assertEqual(len(db), 0)

        db.add_content('25235', 'i325')
        db.add_content('25255', '325')
        db.add_content('25435', '25')
        self.assertEqual(len(db), 3)

        db.delete_id('25435')
        self.assertEqual(len(db), 2)

        db.delete_all()
        self.assertEqual(len(db), 0)

    def test_get_all(self):
        db = StateManager("test.db")
        db.delete_all()

        db.add_content('25235', 'i325')
        db.add_content('25255', '325')
        db.add_content('25435', '25')

        data = db.get_all()
        self.assertEqual(data, [['25235', 'i325', ''], ['25255', '325', ''], ['25435', '25', '']])

    def test_get_info(self):
        db = StateManager("test.db")
        db.delete_all()

        db.add_content('25235', 'i325')
        db.add_content('25255', '325')
        db.add_content('25435', '25')
        inf = db.get_info('25235')
        self.assertEqual(inf, ['', 'i325'])
        inf = db.get_info('25435')
        self.assertEqual(inf, ['', '25'])

    def tearDown(self):
        os.remove("test.db")