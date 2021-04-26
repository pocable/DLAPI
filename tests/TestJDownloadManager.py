from dlapi.JDownloadManager import JDownloadManager
import unittest
import json
import os

# These test cases require the environment file and are indeed very slow.
# Please note that these tests will start a download for Abraham Lincoln 1930
# if you have a media/test directory. This was the first public domain movie
# I could find.
class TestJDownloadManager(unittest.TestCase):

    # Setup the environment for the tests.
    def setUp(self):
        self.conf = None
        f = open('DLAPI_KEYS_START.txt', 'r')
        item = f.read()
        f.close()
        self.conf = json.loads(item)

        for item in self.conf.keys():
            os.environ[item] = self.conf[item]

        self.mngr = JDownloadManager(self.conf['JD_USER'], self.conf['JD_PASS'], self.conf['JD_DEVICE'])

    # Test to see if the device was created properly.
    def test_device_conection(self):
        self.assertEqual(self.conf['JD_DEVICE'], self.mngr.get_device().name)

    # Test that the manager download works.
    def test_download(self):
        result = self.mngr.download(['https://real-debrid.com/d/2ORZVLBF6KKJC'], 'test')
        self.assertEqual(list(result.keys()), ['id'])

    # Test to see if when we call download after its disconnection it will work as intended.
    # When it works, it only returns the id as a result key. Quick check.
    def test_disconnection_reconnect_jd(self):
        self.mngr.get_jd().disconnect()
        result = self.mngr.download(['https://real-debrid.com/d/2ORZVLBF6KKJC'], 'test')
        self.assertEqual(list(result.keys()), ['id'])
