from dlapi.managers import JDownloadManager
import unittest
import json
import os

class TestJDownloadManager(unittest.TestCase):
    """
    Test cases for the JDownloadManager

    These test cases require the environment file and are indeed very slow.
    Please note that these tests will start a download for Abraham Lincoln 1930
    and Africa Screams 1949 if you have a media/test directory. 
    This was the first public domain movie I could find.

    NOTE: These tests may require you to remove them from JDownloader as if its
    a duplicate it will ask you if its ok.
    """

    # Setup the environment for the tests.
    def setUp(self):
        self.mngr = JDownloadManager(os.environ['JD_USER'], os.environ['JD_PASS'], os.environ['JD_DEVICE'])

    # Test to see if the device was created properly.
    def test_device_conection(self):
        self.assertEqual(os.environ['JD_DEVICE'], self.mngr.get_device().name)

    # Test that the manager download works.
    def test_download(self):
        result = self.mngr.download([os.environ['TEST_RD_LINK_ONE']], 'test')
        self.assertEqual(list(result.keys()), ['id'])

    # Test to see if when we call download after its disconnection it will work as intended.
    # When it works, it only returns the id as a result key. Quick check.
    def test_disconnection_reconnect_jd(self):
        self.mngr.get_jd().disconnect()
        result = self.mngr.download([os.environ['TEST_RD_LINK_TWO']], 'test')
        self.assertEqual(list(result.keys()), ['id'])
