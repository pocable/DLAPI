import unittest
from dlapi.managers import RDManager, JDownloadManager
from dlapi.utilclasses import EventDictionary
import logging
import json, os

class TestRDManager(unittest.TestCase):
    """
    Test the Real Debrid Manager class

    NOTE: This will flood your real debrid with download requests for
    night of the living dead. Please remember to clean them out of your torrents on the website 
    (https://real-debrid.com/torrents) 
    
    Also, since RD has its own internal ID system the id below for the 
    test_get_download_urls_might_fail fuction might fail since I think they reuse them.
    """

    def setUp(self):
        self.conf = None
        f = open('DLAPI_KEYS_START.txt', 'r')
        item = f.read()
        f.close()
        self.conf = json.loads(item)

        for item in self.conf.keys():
            os.environ[item] = self.conf[item]

        self.jmanager = JDownloadManager(self.conf['JD_USER'], self.conf['JD_PASS'], self.conf['JD_DEVICE'])
        self.rmanager = RDManager(self.conf['RD_KEY'], logging.getLogger(), self.jmanager)
    
    # Test sending a link to rd and getting download urls at once.
    def test_get_rd_download_urls(self):
        res = self.rmanager.send_to_rd("http://google.ca/")
        self.assertEqual(res[0], False)
        res = self.rmanager.send_to_rd("magnet:?xt=urn:btih:11ea02584fa6351956f35671962ab46354d99060")
        self.assertEqual(res[0], True)

    # Test grabbing the download urls from a provided RDID. Note that this may fail as ID's change
    def test_get_download_urls_might_fail(self):
        self.assertEqual(self.rmanager.get_rd_download_urls("1"), [])
        self.assertNotEqual(self.rmanager.get_rd_download_urls("CIAVUBALLLNLS"), [])

    # Test downloading a provided ID from RD. Note that this may fail as the ID's change
    def test_download_id_might_fail(self):
        result = self.rmanager.download_id("CIAVUBALLLNLS", "test")
        self.assertEqual(list(result.keys()), ['id'])
        self.assertIsNotNone(result['id'])

    # Test the rd listener
    def test_rd_listener(self):
        
        # Useless callback
        def callback(x, y, z):
            pass

        ed = EventDictionary(callback)
        ed['CIAVUBALLLNLS'] = 'test'

        # Run listener to check and find file
        res = self.rmanager.rd_listener(ed)
        self.assertTrue(res)

        # Check and see if we are no longer watching the movie
        self.assertEqual(ed, {})
        