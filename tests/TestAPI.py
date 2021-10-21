
import unittest
import os
from dlapi import app, state_manager

class TestAPI(unittest.TestCase):
    """
    Test cases to test the main API function calls. This uses the flask client to test.
    NOTE: These test cases require all of the functionality to be enabled.
    NOTE: State is cleared from these tests.
    """
    def setUp(self):

        # As these are used in two test cases, might as well.
        # These are urls that require authentication to be used and need to be tested so that un-authorized access is not allowed.
        state_manager.clear()
        self.post_urls = ['/api/v1/content']
        self.delete_urls = ['/api/v1/content', '/api/v1/content/all']
        self.get_urls = ['/api/v1/content/all', '/api/v1/content/check', '/api/v1/corsproxy', '/api/v1/jackett/search']

    def tearDown(self):
        state_manager.clear()

    # Test calling to generate a token
    # POST /api/v1/authenticate
    def test_valid_token(self):
        with app.test_client() as c:
            response = c.post('/api/v1/authenticate', json={'userpass': os.environ['USER_PASS']})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(list(data.keys()), ['token'])

    # Test accessing authenticated areas as a non authenticated user
    # Tests all urls in setUp
    def test_accessing_authenticated_areas_as_non_authenticated(self):
        with app.test_client() as c:
            for post_url in self.post_urls:
                response = c.post(post_url)
                self.assertEqual(response.status_code, 401)

            for delete_url in self.delete_urls:
                response = c.delete(delete_url)
                self.assertEqual(response.status_code, 401)
                
            for get_url in self.get_urls:
                response = c.get(get_url)
                self.assertEqual(response.status_code, 401)

    # Same as above, but instead we use the API_KEY as authentication and should no longer get 401
    # Tests all urls in setUp
    def test_accessing_authenticated_areas_as_authenticated(self):
        with app.test_client() as c:
            for post_url in self.post_urls:
                response = c.post(post_url, headers={'Authorization': os.environ['API_KEY']})
                self.assertNotEqual(response.status_code, 401)

            for delete_url in self.delete_urls:
                response = c.delete(delete_url, headers={'Authorization': os.environ['API_KEY']})
                self.assertNotEqual(response.status_code, 401)
                
            for get_url in self.get_urls:
                response = c.get(get_url, headers={'Authorization': os.environ['API_KEY']})
                self.assertNotEqual(response.status_code, 401)

    # Same as above, but instead we use the USER_KEY as authentication and should no longer get 401
    # POST /api/v1/authenticate, and all urls above
    def test_accessing_authenticated_areas_as_authenticated_user(self):
        with app.test_client() as c:

            # Authenticate with USER_PASS just like test_auth_is_valid_deauth
            response = c.post('/api/v1/authenticate', json={'userpass': os.environ['USER_PASS']})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(list(data.keys()), ['token'])
            token = data['token']

            for post_url in self.post_urls:
                response = c.post(post_url, headers={'Authorization': token})
                self.assertNotEqual(response.status_code, 401)

            for delete_url in self.delete_urls:
                response = c.delete(delete_url, headers={'Authorization': token})
                self.assertNotEqual(response.status_code, 401)
                
            for get_url in self.get_urls:
                response = c.get(get_url, headers={'Authorization': token})
                self.assertNotEqual(response.status_code, 401)

    # Test authenticating, is_valid, and de authenticating 
    # POST /api/v1/authenticate, POST /api/v1/authenticate/validtoken, POST /api/v1/authenticate/closesession
    def test_auth_is_valid_deauth(self):
        with app.test_client() as c:

            # Authenticate
            response = c.post('/api/v1/authenticate', json={'userpass': os.environ['USER_PASS']})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(list(data.keys()), ['token'])

            # Check if its valid
            response = c.post('/api/v1/authenticate/validtoken', json={'token': data['token']})
            self.assertEqual(response.status_code, 200)
            valid = response.get_json()
            self.assertEqual(list(valid.keys()), ['is_valid'])
            self.assertTrue(valid['is_valid'])

            # Close the session
            response = c.post('/api/v1/authenticate/closesession', json={'token': data['token']})
            self.assertEqual(response.status_code, 200)

            # Check if its no longer valid
            response = c.post('/api/v1/authenticate/validtoken', json={'token': data['token']})
            self.assertEqual(response.status_code, 200)
            valid = response.get_json()
            self.assertEqual(list(valid.keys()), ['is_valid'])
            self.assertFalse(valid['is_valid'])

    # Test the cors proxy with a request to example.com
    # GET /api/v1/corsproxy
    def test_cors_proxy(self):
        with app.test_client() as c:
            
            # Try and get example.com html
            response = c.get('/api/v1/corsproxy?url=http://example.com/', headers={'Authorization': os.environ['API_KEY']})
            self.assertEqual(response.status_code, 200)
            content = response.get_data()
            self.assertEqual(content[:15], b'<!doctype html>')

    # Test the Jackett api with a query of test and category of 8000
    # GET /api/v1/jackett/
    def test_jackett_search(self):
        with app.test_client() as c:

            # Unfortunetly it is hard to test as jackett might return different things depending on the torrents.
            # Here we just check that its returning results with a good status code.
            response = c.get('/api/v1/jackett/search?query=test&categories=8000', headers={'Authorization': os.environ['API_KEY']})
            self.assertEqual(response.status_code, 200)
            content = response.get_data()
            self.assertIsNotNone(content)

    # Test deleting specific and all content from DLAPI
    # DELETE /api/v1/content, DELETE /api/v1/content/all
    def test_delete_content(self):
        with app.test_client() as c:
            state_manager.clear()
            state_manager.add_content('test', '123')
            state_manager.add_content('test2', '456')

            # Test delete one
            response = c.delete('/api/v1/content', json={'id': 'test'}, headers={'Authorization': os.environ['API_KEY']})
            self.assertEqual(response.status_code, 200)

            self.assertEqual(len(state_manager), 1)
            self.assertEqual(state_manager.get_info('test2'), ['', '456'])

            # Test delete all
            state_manager.add_content('test3', '789')
            state_manager.add_content('test4', '789')
            response = c.delete('/api/v1/content/all', headers={'Authorization': os.environ['API_KEY']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(state_manager), 0)

    # Test grabbing all content from the server
    # GET /api/v1/content/all
    def test_content_getting(self):
        with app.test_client() as c:
           
            state_manager.clear()
            state_manager.add_content('test', '123')
            state_manager.add_content('test2', '456')
            
            response = c.get('/api/v1/content/all', headers={'Authorization': os.environ['API_KEY']})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(state_manager.get_all_as_dict(), data)

            state_manager.delete_id('test')
            response = c.get('/api/v1/content/all', headers={'Authorization': os.environ['API_KEY']})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(state_manager.get_all_as_dict(), data)

            state_manager.delete_id('test2')
            response = c.get('/api/v1/content/all', headers={'Authorization': os.environ['API_KEY']})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(state_manager.get_all_as_dict(), data)

    # Test posting content to be managed by rdmanager to the server
    # POST /api/v1/content
    @unittest.skipIf('TEST_MAGNET' not in os.environ, "TEST_MAGNET not defined in environment.")
    def test_posting_magnet(self):
        with app.test_client() as c:
            state_manager.clear()
            response = c.post('/api/v1/content', json={'magnet_url': os.environ['TEST_MAGNET'],
             'title': 'Test Magnet File', 'path': '/test'}, headers={'Authorization': os.environ['API_KEY']})

            self.assertEqual(response.status_code, 200)

            # If I dont do this there is a very small chance rd_listener can execute which
            # would cause the JDownloadManager to trigger a download and remove it from the system which would
            # fail this test case.
            data = state_manager.get_all()
            state_manager.clear()
            _, path, title = data[0]

            # Test that our values are properly in the system. Cannot test for key as it is the RD ID and changes
            self.assertEqual(path, '/test')
            self.assertEqual(title, 'Test Magnet File')
            
            


