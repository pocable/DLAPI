from datetime import date, timedelta
import secrets
from dlapi.utilclasses import Session, EventDictionary, DictionaryEventType
from myjdapi.myjdapi import Jddevice, Myjdapi
import functools
from flask import request
import requests
import json
import os
import logging

class JDownloadManager():
    """
    Controller class for managing JDownload to download RD Links
    Attributes:
        username: The user's JDownloader username
        password: The user's JDownloader password
        device_name: The device name defined in JDownloader on the client
    """

    def __init__(self, username: str, password: str, device_name: str):
        self.username = username
        self.password = password
        self.device_name = device_name
        self._initialize_session()

    """
    Download the given urls to the path provided
    urls: List of urls to download
    path: String of the path
    returns: Dictionary 
    """
    def download(self, urls: list, path: str) -> dict:
        
        # Check to see if we are connected, if not try to reconnect, and at worse connect from the start.
        # Documentation on the add_links function is sketchy, so if it works it should return a dictionary.
        self._restart_session()
        result = self.device.linkgrabber.add_links([{"autostart": True, "links": '\n'.join(urls), "destinationFolder": path + "", "overwritePackagizerRules": True}])

        # Got a boolean result once so to prevent any incorrect returns I will return {}.
        # This is an issue with myjdapi
        if type(result) != dict:
            return {}

        return result

    def get_device(self) -> Jddevice:
        return self.device

    def get_jd(self) -> Myjdapi:
        return self.jd

    """
    Refresh the session with JDownloader
    """
    def _restart_session(self):
        if self.jd.is_connected():
            self.jd.reconnect()
        else:
            self.jd.connect(self.username, self.password)
            self.jd.update_devices()
            self.device = self.jd.get_device(self.device_name)

    """
    Starts a session with JDownloader. Called on construction of this class
    """
    def _initialize_session(self):
        jd = Myjdapi()
        jd.set_app_key("DLAPI")
        jd.connect(self.username, self.password)
        jd.update_devices()
        device = jd.get_device(self.device_name)
        self.jd = jd
        self.device = device
        return jd, device

# Class to handle the management of user sessions with the application.
class SessionManager():
    """
    Class to handle the management of user sessions with the application
    Attributes:
        expiry_days: number of days until we expire a session
        ip_sessions: dictionary to keep track of sessions
    """
    def __init__(self, expiry_days: int):
        self.expiry_days = expiry_days
        self.ip_sessions = {}

    """
    Close a provided session
    ip: The ip address
    token: The token given to the ip to terminate
    returns: boolean if a session was closed or not
    """
    def close_session(self, ip: str, token: str) -> bool:
        if ip in self.ip_sessions:
            for session in self.ip_sessions[ip]:
                if session.get_token() == token:
                    self.ip_sessions[ip].remove(session)
                    return True

            # If there are no remaining sessions at the ip, remove it.
            if len(self.ip_sessions[ip]) == 0:
                del self.ip_sessions[ip]
        return False

    """
    Check for expired sessions and remove them from the session list
    NOTE: This function can be slow with a massive load of people.
    In reality though there shouldn't be 50+ connections per houseold IP.
    """
    def remove_expired_sessions(self):
        current_time = date.today()
        for ip in self.ip_sessions:

            # For each session in the ip, validate its time.
            for session in self.ip_sessions[ip]:
                if session.get_expiry() < current_time:
                    self.ip_sessions[ip].remove(session)
        
        keys = list(self.ip_sessions.keys())
        for i in range(0, len(self.ip_sessions)):

            # If there are no remaining sessions at the ip, remove it.
            if len(self.ip_sessions[keys[i]]) == 0:
                del self.ip_sessions[keys[i]]
                i -= 1

    """
    Authenticate a user given their ip and the token they provided
    token: The token the user provided
    ip: The IP recieved from the API request
    returns: boolean if they are authenticated or not
    """
    def authenticate_user(self, ip: str, token: str) -> bool:

        # If the token provided is the API key, let them through!
        if token == os.environ['API_KEY']:
            return True

        # Check if the ip is in the sessions, then iterate over all sessions at the house
        # until either it finds a valid session or it returns False        
        if ip in self.ip_sessions:
            sessions = self.ip_sessions[ip]
            for session in sessions:
                if session.get_token() == token and session.get_ip() == ip:
                    
                    # Verify the token is not expiried
                    if session.get_expiry() < date.today():
                        return False

                    return True
        
        return False

    """
    Create a session for the given ip address
    ip: The ip address to provide a session token
    returns: A string token the user needs to authenticate
    """
    def create_session(self, ip: str) -> str:
        token = secrets.token_urlsafe()
        s = Session(ip, token, date.today() + timedelta(days=self.expiry_days))
        if ip in self.ip_sessions:
            self.ip_sessions[ip].append(s)
        else:
            self.ip_sessions[ip] = [s]

        return token

    def get_sessions(self) -> dict:
        return self.ip_sessions

    """
    Manual session adding given a session object
    ip: The ip address to add the session to
    session: The session
    """
    def _add_session(self, ip: str, session: Session):
        if ip in self.ip_sessions:
            self.ip_sessions[ip].append(session)
        else:
            self.ip_sessions[ip] = [session]

    """
    Decorator to require validation in order for the code to be ran.
    NOTE: Requires a proper request object from flask.
    """
    def requires_authentication(self, func):
        @functools.wraps(func)
        def wrapper_validate(*args, **kwargs):
            if 'Authorization' in request.headers.keys():
                if self.authenticate_user(request.remote_addr, request.headers['Authorization']):
                    return func(*args, **kwargs)
            return {'Error' : 'Authentication Failed'}, 401
        return wrapper_validate

class RDManager():
    """
    Manager for RealDebrid communication.
    Attributes:
        _server: The real debrid server
        _header: The authorization header
        _logger: Logger passed into to monitor issues with RD
        jdownloader: The JDownloadManager used to download what we need
    """

    def __init__(self, api_key: str, logger: logging.Logger, jdownloader: JDownloadManager):
        self._server = "https://api.real-debrid.com/rest/1.0/"
        self._header = {'Authorization': 'Bearer ' + api_key }
        self._logger = logger
        self.jdownloader = jdownloader

    """
    Get the real debrid download url from the website
    id: The real debrid ID to get all of the links for
    returns: The links associated with the identifier
    """
    def get_rd_download_urls(self, id: str) -> list:
        req = requests.get(self._server + "torrents/info/%s" %  id, headers=self._header)
        if(req.status_code == 401 or req.status_code == 403):
            return []
        res = json.loads(req.text)

        if 'error' in res:
            return []
        
        return res['links']

    """
    Send a magnet url to realdebrid to start the download process.
    magnet: The magnet url url.
    returns: A tuple of (bool, id/error)
    """
    def send_to_rd(self, magnet_url: str) -> tuple:
        data = {'magnet': magnet_url}
        req = requests.post(self._server + "torrents/addMagnet", data=data, headers=self._header)
        if req.status_code != 201:
            return (False, "Error in sending magnet link to RD. Code: %d, Text: %s" % (req.status_code, req.text))
        else:
            res = json.loads(req.text)
            id = res['id']
            req = requests.post(self._server + "torrents/selectFiles/%s" % id, data={'files': "all"}, headers=self._header)
            if req.status_code != 204 and req.status_code != 202:
                return (False, "Error in sending magnet link to RD. Code: %d, Text: %s" % (req.status_code, req.text))
            else:
                return (True, id)

    """
    Download the provided real debrid ID using JDownloader
    id: The realdebrid internal id.
    """
    def download_id(self, id : str, path: str) -> dict:
        urls = self.get_rd_download_urls(id)
        download_urls = []
        for url in urls:
            req = requests.post(self._server + "unrestrict/link", data={'link': url}, headers=self._header)
            res = json.loads(req.text)

            # The status code returned meant we had a bad token or account was locked. Nothing we can do.
            if(req.status_code == 401 or req.status_code == 403):
                self._logger.error("Failed to connect to real debrid. Error code: %s. Out of premium/banned?" % (str(req.status_code)))
                continue

            download_urls.append(res['download'])

        return self.jdownloader.download(download_urls, path)

    def _download_id_and_remove_if_success(self, id: str, path: str, eventdict: EventDictionary) -> dict:
        self.download_id(id, path)
        if id in eventdict.keys():
            del eventdict[id]

    """
    Function to check with real debrid to see if
    """
    def rd_listener(self, watched_content: EventDictionary) -> bool:
        
        # If there is nothing to watch, why poll RD?
        if len(watched_content) == 0:
            return True

        # Try to get RD torrents list
        try:
            req = requests.get(self._server + "torrents", headers=self._header)
        except:
            # Most likely polling too quicly. Just wait for the next poll
            self._logger.warning("Failed to get the torrent list from Real-Debrid. Might be polling too fast.")
            return False

        # Check if we failed to connect.
        if(req.status_code == 401 or req.status_code == 403):
            self._logger.error("Failed to connect to real debrid. Error code: %s. Out of premium/banned?" % (str(req.status_code)))
            return False

        res = json.loads(req.text)

        # For each of the different torrent files we obtained
        for file in res:

            # If the file is being watched, check status
            if file['id'] in watched_content.keys():

                # If its downloaded and ready, process and remove for next cycle. 
                # Otherwise if error log and remove.
                if file['status'] == 'downloaded':
                    self._download_id_and_remove_if_success(file['id'], watched_content[file['id']], watched_content)
                elif file['status'] == 'magnet_error':
                    self._logger.error("Magnet error on torrent with id: %s, path: %s" 
                        % (file['id'], watched_content[file['id']]))
                    del watched_content[file['id']]
                    continue
                elif file['status'] == 'virus':
                    self._logger.error("Virus detected on torrent with id: %s, path: %s" 
                        % (file['id'], watched_content[file['id']]))
                    del watched_content[file['id']]
                    continue
                elif file['status'] == 'error':
                    self._logger.error("Generic error on torrent with id: %s, path: %s" 
                        % (file['id'], watched_content[file['id']]))
                    del watched_content[file['id']]
                    continue
                elif file['status'] == 'dead':
                    self._logger.error("Dead torrent with id: %s, path: %s" 
                        % (file['id'], watched_content[file['id']]))
                    del watched_content[file['id']]
                    continue

        return True


class StateManager(EventDictionary):
    """
    Manager for controlling the internal state file saved when needed.

    Attributes:
        config_path: The path where the file is saved at for the state.
    """

    def __init__(self, config_path: str):
        super().__init__(self._callback)
        self.config_path = config_path

    """
    Internal callback to save the state everytime we are updated.
    """
    def _callback(self, e: str, v: str, d: DictionaryEventType):
        self.save_state()

    """
    Save our state to the file.
    """
    def save_state(self):
        f = open(self.config_path, 'w')
        f.write(json.dumps(self))
        f.close()

    """
    Load state from the file on the path.
    """
    def load_state(self):
        f = open(self.config_path, 'r')
        self.update(json.loads(f.read()))
        f.close()