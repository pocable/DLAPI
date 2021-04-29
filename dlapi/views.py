from dlapi import (app, limiter, logger, session_manager,
 real_debrid_manager, jdownload_manager, state_manager)

from flask import request, jsonify
import requests
import os
from urllib.parse import unquote_plus

# Endpoint to add content to be watched
@app.route('/api/v1/content', methods=['POST'])
@session_manager.requires_authentication
def add_content():
    id = None
    title = None
    content = request.get_json(silent=True, force=True)

    if content == None:
        return {'Error' : 'No JSON provided'}, 400

    if 'magnet_url' in content:
        magnet_url = content['magnet_url']
    elif 'id' in content:
        id = (True, content['id'])
    elif 'url' in content:

        # Resolve the url to get the magnet link
        url = content['url']
        if url == None:
            return{'Error' : "No link was provided"}, 400
            
        try:
            url = requests.get(url).url
        except requests.exceptions.InvalidSchema as e:
            # Remove error intro
            url = str(e)[39:]
            url = url[:-1]

        # Set magnet url for later.
        magnet_url = url
    else:
        content = {'Error' : 'magnet_url is missing from post.'}
        return content, 400
    
    if 'path' in content:
        path = content['path']
    else:
        content = {'Error' : 'Path is missing from post.'}
        return content, 400

    if 'title' in content:
        title = content['title']

    # Send magnet link to be downloaded
    if id == None:
        id = real_debrid_manager.send_to_rd(magnet_url)
    if id[0] == False:
        return {'Error': id[1]}, 417

    package = {'path':path}
    if title != None:
        package['title'] = title

    
    state_manager[id[1]] = package
    return {}, 200

# Endpoint for deleting content from being watched
@app.route('/api/v1/content', methods=['DELETE'])
@session_manager.requires_authentication
def remove_content():
    content = request.get_json(silent=True, force=True)
    if content == None:
        return {'Error' : 'No JSON provided'}, 400
    if 'id' in content:
        id = content['id']
    else:
        content = {'Error' : 'ID is missing from post.'}
        return content, 400

    # If we have the id, delete it.
    if id in state_manager.keys():
        del state_manager[id]
        return {}, 200
    else:
        return {'Error' : 'ID is not in the watched list.'}, 410

# Endpoint to get all watched content on RD
@app.route('/api/v1/content/all', methods=['GET'])
@session_manager.requires_authentication
def get_content():
    return jsonify(state_manager)

# Endpoint to get all watched content on RD
@app.route('/api/v1/content/all', methods=['DELETE'])
@session_manager.requires_authentication
def delete_all_content():
    state_manager.clear()
    return {}, 200

# Endpoint to immedietly check for downloads (calls rd_listener)
@app.route('/api/v1/content/check', methods=['GET'])
@session_manager.requires_authentication
def trigger_check():
    real_debrid_manager.rd_listener(state_manager)
    return {}, 200

# CORS proxy.
@app.route('/api/v1/corsproxy', methods=['GET'])
@session_manager.requires_authentication
def CORS_proxy():
    if not 'ENABLE_CORS_PROXY' in os.environ:
        return {'Error': 'CORS proxy is not enabled.'}, 410

    if os.environ['ENABLE_CORS_PROXY'].lower() != 'true':
        return {'Error': 'CORS proxy is not enabled.'}, 410
    
    # Get url to forward to
    url = request.args.get('url')
    if url == None:
        return {'Error': 'URL was not provided'}, 400
    
    # Fix quotations and request a get to the link
    base = unquote_plus(request.base_url)
    link = unquote_plus(request.url)
    req = requests.get(link.replace(base, '')[5:])

    # Return the exact result.
    return req.text, req.status_code

# Jackett Section, its pretty much the CORS proxy above but with jackett stuff and targeted at search.
@app.route('/api/v1/jackett/search', methods=['GET'])
@session_manager.requires_authentication
def search_jackett():
    if 'JACKETT_URL' not in os.environ or 'JACKETT_API_KEY' not in os.environ:
        return {'Error': 'Jackett module is not enabled.'}, 410

    # Get query and categories
    query = request.args.get('query')
    if query == None:
        return {'Error': 'Query was not provided'}, 400

    categories = request.args.get('categories')
    if categories == None:
        return {'Error': 'Categories was not provided'}, 400

    categories = '&Category=' + '&Category='.join(categories.split(','))

    # Build the URL to connect to the JACKETT API.
    build_query = os.environ['JACKETT_URL'] + "api/v2.0/indexers/all/results/?apikey=" + os.environ['JACKETT_API_KEY'] + categories + '&t=search&limit=1000&Query=' + query
    
    # Fix quotations and request a get to the link.
    req = requests.get(build_query)

    # Implement the jackett search functionality here.
    return req.text, req.status_code


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

@app.route('/api/v1/authenticate/validtoken', methods=['POST'])
def is_valid_token():
    if not 'USER_PASS' in os.environ:
        return {'Error': 'Sessioning is not enabled. This call is not required.'}, 410

    content = request.get_json(silent=True, force=True)
    if content == None:
        return {'Error' : 'No JSON provided'}, 400

    # Get the token if its there
    if 'token' in content:
        token = content['token']
    else:
        return {'Error': 'token was not provided'}, 400

    # Check each session for ip and token equal. If it is the token is valid.
    if session_manager.authenticate_user(request.remote_addr, token):
        return {'is_valid': True}

    return {'is_valid': False}

@app.route('/api/v1/authenticate/closesession', methods=['POST'])
def close_session():
    if not 'USER_PASS' in os.environ:
        return {'Error': 'Sessioning is not enabled. This call is not required.'}, 410

    content = request.get_json(silent=True, force=True)
    if content == None:
        return {'Error' : 'No JSON provided'}, 400

    # Get the token if its there
    if 'token' in content:
        token = content['token']
    else:
        return {'Error': 'token was not provided'}, 400

    # Close the session.
    session_manager.close_session(request.remote_addr, token)

    return {}, 200
