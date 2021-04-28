from dlapi import (app, limiter, logger, session_manager,
 real_debrid_manager, jdownload_manager)

from flask import request, jsonify
import requests
import os

# Temp calls just to test if the new structure works. This will be modified
# in the next commit to have all the callbacks, the API should be functional
# and able to be merged into beta for the test release.

@app.route('/')
def test_main():
    return "Hello World!"

@app.route('/test')
@session_manager.requires_authentication
def test_auth():
    return "AUTHENTICATED!"

@app.route('/api/v1/authenticate', methods=['POST'])
@limiter.limit("5/minute")
def authenticate():

    if not 'USER_PASS' in os.environ:
        return {'Error': 'Sessioning is not enabled. This call is not required.'}, 410

    content = request.get_json(silent=True, force=True)
    if content == None:
        return {'Error' : 'No JSON provided'}, 400

    # Get the userpass
    if 'userpass' in content:
        userpass = content['userpass']
    else:
        return {'Error': 'userpass was not provided'}, 400

    # If it matches the userpass or the api key, create a session.
    if userpass == os.environ['USER_PASS'] or userpass == os.environ['API_KEY']:
        return {'token': session_manager.create_session(request.remote_addr)}, 200


    return {'Error' : 'Authentication Failed'}, 401
