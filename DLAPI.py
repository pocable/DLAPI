# Api Polling Imports
import json
import requests
import time
import myjdapi

# Flask Imports
import flask
from flask import request, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler

# System imports
import sys
import os

# Shutdown Safety
import atexit

# Logging
import logging

# URL fixing
from urllib.parse import unquote_plus

# Timing
from datetime import date, timedelta

# Sessions
import secrets

# Limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# https://my.jdownloader.org/
JDOWNLOADER_USER = os.environ['JD_USER']
JDOWNLOADER_PASS = os.environ['JD_PASS']
JDOWNLOADER_DEVICE = os.environ['JD_DEVICE']

# https://real-debrid.com/apitoken
REAL_DB_KEY = os.environ['RD_KEY']

# CORS PROXY if enabled for connecting to jackett via webapp.
ENABLE_CORS_PROXY = False
if 'ENABLE_CORS_PROXY' in os.environ:
    try:
        ENABLE_CORS_PROXY = os.environ['ENABLE_CORS_PROXY'].lower() == 'true'
    except:
        pass


# Jackett API (Merging insecure jdrd into dlapi). Made as optional module.
ENABLE_JACKETT = False
if all (envar in os.environ for envar in ('JACKETT_URL', 'JACKETT_API_KEY')):
    JACKETT_URL = os.environ['JACKETT_URL']
    JACKETT_API_KEY = os.environ['JACKETT_API_KEY']
    ENABLE_JACKETT = True

# Sessioning Module
ENABLE_SESSIONING = False
SESSION_PASSWORD = ""
sessions = []
if 'USER_PASS' in os.environ:
    SESSION_PASSWORD = os.environ['USER_PASS']
    ENABLE_SESSIONING = True

SESSION_EXPIRY_DAYS = 1
if 'SESSION_EXPIRY_DAYS' in os.environ:
    SESSION_EXPIRY_DAYS = int(os.environ['SESSION_EXPIRY_DAYS'])


# Rate at which RD is polled for downloads. Keep > 250
# RD will not finish a torrent under 2.5 minutes and
# I do not want to poll their servers too much.
rate_delay = 150

# Save Interval
save_interval = 60

# Session check interval
session_interval = 1200

# Should not be changed
REAL_DB_SERVER = "https://api.real-debrid.com/rest/1.0/"
header = {'Authorization': 'Bearer ' + REAL_DB_KEY }

API_KEY = os.environ['API_KEY']
device = None

# Config Folder
config_folder = "./dlconfig/"

# Internal global items and flask configuration
watched_content = {}
app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = False
device = None
first_load = False
jd = None

# Rate Limiting
limiter = Limiter(app, key_func=get_remote_address)

# Logging Setup
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# Threading Configuration
rd_thread = None

# Configuration object for scheduling update
class Config(object):
    JOBS = [
        {
            'id': 'RDListener',
            'func': __name__ + ':rd_listener',
            'args': (),
            'trigger': 'interval',
            'seconds': rate_delay
        },
        {
            'id': 'SaveFunc',
            'func': __name__ + ':save_state',
            'args': (),
            'trigger': 'interval',
            'seconds': save_interval
        },
        {
            'id': 'SessionManager',
            'func': __name__ + ":session_manager",
            'args': (),
            'trigger': 'interval',
            'seconds': session_interval
        }
    ]

    SCHEDULER_API_ENABLED = True

# Class representing a user session.
class Session():
    def __init__(self, ip, token, expiry):
        self._ip = ip
        self._token = token
        self._expiry = expiry

    def get_ip(self):
        return self._ip

    def get_token(self):
        return self._token

    def get_expiry(self):
        return self._expiry

"""
Get the real debrid download url from the website
ident: The identifier for the show your looking for.
returns: The links associated with the identifier
"""
def get_rd_download_urls(ident):
    req = requests.get(REAL_DB_SERVER + "torrents/info/%s" %  ident, headers=header)
    if(req.status_code == 401 or req.status_code == 403):
        raise Exception("Failed to get torrent info. Status code: " + str(req.status_code))
    res = json.loads(req.text)
    return res['links']

"""
Send a list of urls to a jdownloader device
device: The jdownload device
urls: The list of urls to download
path: The path to download to.
"""
def jdownload(dev, urls, path):
    global jd
    global device

    try:
        
        # Try add links to the device
        dev.linkgrabber.add_links([{'autostart': True, 'links': '\n'.join(urls),
            'destinationFolder': path + "", "overwritePackagizerRules": True}])
    except:
        
        # Try again with a reconnected jdownload session
        jd, device = setup_jdownload()
        device.linkgrabber.add_links([{'autostart': True, 'links': '\n'.join(urls), 
            'destinationFolder': path + "", "overwritePackagizerRules": True}])

    app.logger.info("Sent movie to jdownloader server with path: %s" % path)

"""
Setup jdownloader using the given username and password
returns: The device to send downloads to.
"""
def setup_jdownload():
    jd = myjdapi.Myjdapi()
    jd.set_app_key("JDRD")
    jd.connect(JDOWNLOADER_USER, JDOWNLOADER_PASS)
    jd.update_devices()
    device = jd.get_device(JDOWNLOADER_DEVICE)
    return jd, device

"""
Get all the download links for a given real debrid url.
url: The real debred url to open.
"""
def get_dl_links(urls):
    download_urls = []
    for url in urls:
        req = requests.post(REAL_DB_SERVER + "unrestrict/link", data={'link': url}, headers=header)
        res = json.loads(req.text)
        if(req.status_code == 401 or req.status_code == 403):
            raise Exception("Failed to get torrent info. Status code: " + str(req.status_code))
        try:
            download_urls.append(res['download'])
        except:
            pass
    return download_urls

"""
Send a magnet url to realdebrid to being downloading.
magnet: The url.
returns: 
"""
def send_to_rd(magnet):
    data = {'magnet': magnet}
    req = requests.post(REAL_DB_SERVER + "torrents/addMagnet", data=data, headers=header)
    if req.status_code != 201:
        return (False, "Error in sending magnet link to RD. Code: %d, Text: %s" 
            % (req.status_code, req.text))
    else:
        res = json.loads(req.text)
        ident = res['id']
        req = requests.post(REAL_DB_SERVER + "torrents/selectFiles/%s" 
            % ident, data={'files': "all"}, headers=header)
        if req.status_code != 204 and req.status_code != 202:
            return (False, "Error in sending magnet link to RD. Code: %d, Text: %s" 
                % (req.status_code, req.text))
        else:
            return (True, ident)

"""
Download the ID provided when it is done by RD
id: The realdebrid internal id.
"""
def download_id(id):
    urls = get_rd_download_urls(id)
    download_urls = []
    for url in urls:
        req = requests.post(REAL_DB_SERVER + "unrestrict/link", data={'link': url}, headers=header)
        res = json.loads(req.text)
        if(req.status_code == 401 or req.status_code == 403):
            app.logger.error("Failed to get torrent info. Status code: " + str(req.status_code))
            continue
        download_urls.append(res['download'])

    # Try and download the movie, if successful then delete ID. Otherwise, don't delete but severe log.
    try:
        jdownload(device, download_urls, watched_content[id]['path'])
        del watched_content[id]
    except Exception as e:
        app.logger.error("Issue in JDownloader: " + str(e))

"""
Poll RD every rate_delay seconds in order to check for updates on torrent statuses
"""
def rd_listener():
    
    # If there is nothing to watch, why poll RD?
    if len(watched_content) == 0:
        return

    # Try to get RD torrents list
    try:
        req = requests.get(REAL_DB_SERVER + "torrents", headers=header)
    except:
        app.logger.error("Request Issue. Maybe polling too quickly?")
        return

    # Check if we failed to connect.
    if(req.status_code == 401 or req.status_code == 403):
        app.logger.error("Failed to connect to real debrid. Error code: " + str(req.status_code))
        return

    res = json.loads(req.text)

    # For each of the different torrent files we obtained
    for file in res:

        # If the file is being watched, check status
        if file['id'] in watched_content.keys():
            # If its downloaded and ready, process and remove for next cycle. 
            # Otherwise if error log and remove.
            if file['status'] == 'downloaded':
                download_id(file['id'])
            elif file['status'] == 'magnet_error':
                app.logger.error("Magnet error on torrent with id: %s, path: %s" 
                    % (file['id'], watched_content[file['id']]))
                del watched_content[file['id']]
                continue
            elif file['status'] == 'virus':
                app.logger.error("Virus detected on torrent with id: %s, path: %s" 
                    % (file['id'], watched_content[file['id']]))
                del watched_content[file['id']]
                continue
            elif file['status'] == 'error':
                app.logger.error("Generic error on torrent with id: %s, path: %s" 
                    % (file['id'], watched_content[file['id']]))
                del watched_content[file['id']]
                continue
            elif file['status'] == 'dead':
                app.logger.error("Dead torrent with id: %s, path: %s" 
                    % (file['id'], watched_content[file['id']]))
                del watched_content[file['id']]
                continue

# Check for expired sessions and remove them from the session list.
def session_manager():
    current_time = date.today()
    for session in sessions:
        if session == None:
            return

        if session.get_expiry() < current_time:
            sessions.remove(session)

"""
Save the current program state.
"""
def save_state():
    if first_load:
        f = open(config_folder + "state.txt", 'w')
        f.write(json.dumps(watched_content))
        f.close()


# Flask Routing

# Endpoint to add content to be watched
@app.route('/api/v1/content', methods=['POST'])
def add_content():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
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
                o_url = content['url']
                url = o_url
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
                id = send_to_rd(magnet_url)
            if id[0] == False:
                return {'Error': id[1]}, 417

            package = {'path':path}
            if title != None:
                package['title'] = title

            watched_content[id[1]] = package
            return {}, 200

    return {'Error' : 'Authentication Failed'}, 401

# Endpoint for deleting content from being watched
@app.route('/api/v1/content', methods=['DELETE'])
def remove_content():

    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            content = request.get_json(silent=True, force=True)
            if content == None:
                return {'Error' : 'No JSON provided'}, 400
            if 'id' in content:
                id = content['id']
            else:
                content = {'Error' : 'ID is missing from post.'}
                return content, 400

            # If we have the id, delete it.
            if id in watched_content.keys():
                del watched_content[id]
                return {}, 200
            else:
                return {'Error' : 'ID is not in the watched list.'}, 410

    return {'Error' : 'Authentication Failed'}, 401

# Endpoint to get all watched content on RD
@app.route('/api/v1/content/all', methods=['GET'])
def get_content():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            return jsonify(watched_content)

    return {'Error' : 'Authentication Failed'}, 401

# Endpoint to get all watched content on RD
@app.route('/api/v1/content/all', methods=['DELETE'])
def delete_all_content():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            watched_content = {}
            return {}, 200

    return {'Error' : 'Authentication Failed'}, 401

# Endpoint to immedietly check for downloads (calls rd_listener)
@app.route('/api/v1/content/check', methods=['GET'])
def trigger_check():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            rd_listener()
            return {}, 200

    return {'Error' : 'Authentication Failed'}, 401

# CORS proxy.
@app.route('/api/v1/corsproxy', methods=['GET'])
def CORS_proxy():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            if not ENABLE_CORS_PROXY:
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

    return {'Error' : 'Authentication Failed'}, 401

# Jackett Section, its pretty much the CORS proxy above but with jackett stuff and targeted at search.
@app.route('/api/v1/jackett/search', methods=['GET'])
def search_jackett():
    if 'Authorization' in request.headers.keys():
        if authenticate_user(request.headers['Authorization'], request.remote_addr):
            if not ENABLE_JACKETT:
                return {'Error': 'Jackett module is not enabled.'}, 410

            # Get query and categories
            query = request.args.get('query')
            if query == None:
                return {'Error': 'query was not provided'}, 400

            categories = request.args.get('categories')
            if categories == None:
                return {'Error': 'categories was not provided'}, 400

            categories = '&Category=' + '&Category='.join(categories.split(','))

            # Build the URL to connect to the JACKETT API.
            build_query = JACKETT_URL + "api/v2.0/indexers/all/results/?apikey=" + JACKETT_API_KEY + categories + '&t=search&limit=1000&Query=' + query
            
            # Fix quotations and request a get to the link.
            req = requests.get(build_query)

            # Implement the jackett search functionality here.
            return req.text, req.status_code

    return {'Error' : 'Authentication Failed'}, 401


@app.route('/api/v1/authenticate', methods=['POST'])
@limiter.limit("5/minute")
def authenticate():

    if not ENABLE_SESSIONING:
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
    if userpass == SESSION_PASSWORD or userpass == API_KEY:
        return {'token': create_session(request.remote_addr)}, 200


    return {'Error' : 'Authentication Failed'}, 401

@app.route('/api/v1/authenticate/validtoken', methods=['POST'])
def is_valid_token():
    if not ENABLE_SESSIONING:
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
    for s in sessions:
        if s.get_ip() == request.remote_addr and s.get_token() == token:
            return {'is_valid': True}

    return {'is_valid': False}

@app.route('/api/v1/authenticate/closesession', methods=['POST'])
def close_session():
    if not ENABLE_SESSIONING:
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
    for s in sessions:
        if s.get_ip() == request.remote_addr and s.get_token() == token:
            sessions.remove(s)
            return {}, 200
    return {}, 200


"""
Create a session given the ip
ip: The user ip
returns: a token for the session.
"""
def create_session(ip):
    token = secrets.token_urlsafe()
    s = Session(ip, token, date.today() + timedelta(days=SESSION_EXPIRY_DAYS))
    sessions.append(s)
    return token


"""
Authenticate the user.
item: either the api key or a user session token
ip: if its a user session token, want the ip to verify.

returns: if the user is authenticated
"""
def authenticate_user(item, ip=None):
    if item == API_KEY:
        return True
    
    if ip != None and ENABLE_SESSIONING:
        for z in sessions:
            if z.get_token() == item and z.get_ip() == ip:
                return True
    
    return False

# Called when the appliation is shutdown. Saves the watched content list for resuming later.
def on_shutdown():
    save_state()

# Check if the system is able to setup jdownloader. If not, retry in 15 seconds.
# With unraid or docker containers that launch on boot, if DLAPI is first this will prevent a
# crash.
device = None
retry_count = 0
retry_max = 5
while retry_count < retry_max:
    retry_count += 1
    try:
        jd, device = setup_jdownload()
        app.logger.info("JDownloader setup succeeded.")
        break
    except myjdapi.myjdapi.MYJDException as e:
        app.logger.info("JDownloader had an issue setting up. Please check your JDownloader configuration or " 
            + "device status. Error: " + str(e) + "\nRetrying in 15 seconds. Attempt %d/%d" % (retry_count, retry_max))
        time.sleep(15)

# If we max out the retrys, exit the application. The device was not found.
if retry_count >= retry_max:
    app.logger.warning("JDownloader failed to setup after %d attempts." % (retry_count))
    sys.exit(4)

# Check if there is a state needing to be loaded.
try:
    f = open(config_folder + "state.txt", 'r')
    watched_content = json.loads(f.read())
    f.close()
except Exception:
    pass

first_load = True

# Setup scheduler for checking RD
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if __name__ == "__main__":
    atexit.register(on_shutdown)
    app.run(host='0.0.0.0', port=4248, debug=True)

def main():
    atexit.register(on_shutdown)
    app.run(host='0.0.0.0', port=4248, debug=True)