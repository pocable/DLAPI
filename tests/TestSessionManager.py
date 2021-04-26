from dlapi.managers import SessionManager
from dlapi.utilclasses import Session
import unittest
from datetime import date, timedelta

class TestSessionManager(unittest.TestCase):
    """
    Test cases for the session manager.
    """

    # Test adding a singular session
    def test_add_session(self):
        mngr = SessionManager(10)
        mngr.create_session('192.168.0.1')
        sessions = mngr.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sessions['192.168.0.1']), 1)
        self.assertEqual(sessions['192.168.0.1'][0].get_ip(), '192.168.0.1')

    # Test adding multiple different sessions
    def test_add_multiple_sessions(self):
        test_ips = ['192.168.0.1', '192.168.0.2', '192.168.0.3']
        mngr = SessionManager(10)

        for ip in test_ips:
            mngr.create_session(ip)

        sessions = mngr.get_sessions()
        self.assertEqual(len(sessions), 3)

        for ip in test_ips:
            self.assertEqual(len(sessions[ip]), 1)
            self.assertEqual(sessions[ip][0].get_ip(), ip)

    # Test adding multiple different sessions at the same ip
    def test_multiple_sessions_at_same_ip(self):
        test_ips = ['192.168.0.1', '192.168.0.2', '192.168.0.3']
        counts = [1, 9, 10]
        mngr = SessionManager(10)

        for i in range(0, len(test_ips)):
            for j in range(0, counts[i]):
                mngr.create_session(test_ips[i])

        sessions = mngr.get_sessions()
        self.assertEqual(len(sessions), 3)

        for i in range(0, len(test_ips)):
            self.assertEqual(len(sessions[test_ips[i]]), counts[i])
            for j in range(0, counts[i]):
                self.assertEqual(sessions[test_ips[i]][j].get_ip(), test_ips[i])

    # Test authenticating with the token.
    def test_authentication(self):
        session = Session('192.168.0.1', 'tokentest', date.today() + timedelta(days=10))
        mngr = SessionManager(10)
        mngr._add_session('192.168.0.1', session)

        # Test single session at ip
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'tokentest'), True)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', ''), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'notatoken'), False)

        session2 = Session('192.168.0.1', 'token2', date.today() + timedelta(days=10))
        mngr._add_session('192.168.0.1', session2)

        # Test multiple session authentication
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'tokentest'), True)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'token2'), True)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', ''), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'notatoken'), False)

        # Test other ip token
        session3 = Session('192.168.0.2', 'zzb', date.today() + timedelta(days=10))
        mngr._add_session('192.168.0.2', session3)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'tokentest'), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'token2'), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'zzb'), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'zzb'), True)

    # Test closing the session and making sure the dictionary updates properly.
    def test_close_session(self):
        session = Session('192.168.0.1', 'tokentest', date.today() + timedelta(days=10))
        session2 = Session('192.168.0.2', 'test', date.today() + timedelta(days=10))
        mngr = SessionManager(10)
        mngr._add_session('192.168.0.1', session)
        mngr._add_session('192.168.0.2', session2)

        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'tokentest'), True)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'test'), True)
        mngr.close_session('192.168.0.1', session.get_token())
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'tokentest'), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'test'), True)

    # Test expiring sessions with remove_expired_sessions and custom sessions.
    def test_expire_sessions(self):
        session = Session('192.168.0.1', 'tokentest', date.today() + timedelta(days=-20))
        session2 = Session('192.168.0.2', 'test', date.today() + timedelta(days=10))
        mngr = SessionManager(10)
        mngr._add_session('192.168.0.1', session)
        mngr._add_session('192.168.0.2', session2)

        sessions = mngr.get_sessions()
        self.assertEqual(len(sessions), 2)

        mngr.remove_expired_sessions()
        sessions = mngr.get_sessions()
        self.assertEqual(len(sessions), 1)
        
        self.assertEqual(mngr.authenticate_user('192.168.0.1', 'tokentest'), False)
        self.assertEqual(mngr.authenticate_user('192.168.0.2', 'test'), True)
        

