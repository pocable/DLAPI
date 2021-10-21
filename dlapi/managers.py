from datetime import date, timedelta
import secrets
from dlapi.utilclasses import Session, EventDictionary, DictionaryEventType
from myjdapi.myjdapi import Jddevice, Myjdapi, MYJDException
import functools
from flask import request
import requests
import json
import os
import logging
import sqlite3

class JDownloadManager():
    """
    Controller class for managing JDownload to download RD Links
    Attributes:
        username: The user's JDownloader username
        password: The user's JDownloader password
        device_name: The device name defined in JDownloader on the client
    """

    def __init__(self, username: str, password: str, device_name: str, logger: logging.Logger = None):
        self.username = username
        self.password = password
        self.device_name = device_name

        # Use default logger if none is provided.
        if logger == None:
            logger = logging.getLogger()

        self.logger = logger
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

        # If the device isn't set return {} and try to download it on the next cycle.
        if self.device == None:
            return {}
        
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

        # Try to reconnect if we can, if there is an exception, restart the connection.
        try:
            if self.jd.is_connected():
                self.jd.reconnect()
                return
        except:
            pass

        self.jd.connect(self.username, self.password)
        self._safe_set_device()

    """
    Starts a session with JDownloader. Called on construction of this class
    """
    def _initialize_session(self):
        jd = Myjdapi()
        jd.set_app_key("DLAPI")
        jd.connect(self.username, self.password)
        self.jd = jd
        self._safe_set_device()
        return jd, self.device

    """
    Get the JD device but catch and set it to None. This will cause a re-attempt later on.
    """
    def _safe_set_device(self):
        self.jd.update_devices()
        try:
            self.device =  self.jd.get_device(self.device_name)
        except MYJDException:
            self.logger.warn('Device %s was not found. Will try again but double check the device name.' % self.device_name)
            self.device = None

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
    """
    def remove_expired_sessions(self):
        current_time = date.today()
        keys = list(self.ip_sessions.keys())
        for i in range(0, len(self.ip_sessions)):
            ip = keys[i]
            
            # For each session in the ip, validate its time.
            for session in self.ip_sessions[ip]:
                if session.get_expiry() < current_time:
                    self.ip_sessions[ip].remove(session)

            # If there are no remaining sessions at the ip, remove it.
            if len(self.ip_sessions[ip]) == 0:
                del self.ip_sessions[ip]
                i -= 1
                continue


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


class FileStateManager(EventDictionary):
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

class StateManager():
    """
    StateManager using sqlite3 database in order to maintain watched content.
    Due to JSON not having a tuple definition, all tuples returned from sqlite are
    converted into a list.

    Attributes:
        _con: Connection to the database
        _cur: Database cursor
    """
    def __init__(self, db_file: str):
        self.db_file = db_file
        with sqlite3.connect(db_file) as _con:
            _cur = _con.cursor()

            # Create the table if it does not exist.
            _cur.execute('''
            CREATE TABLE IF NOT EXISTS content (
                "id"	TEXT NOT NULL UNIQUE,
                "path"	TEXT NOT NULL,
                "title"	TEXT,
                PRIMARY KEY("id")
            )''')
            _con.commit()


    """
    Internal decorator to open a connection to the database.
    All actions are commited and the conneciton is closed after every call.
    Note: Without copy and pasting, I thought this was the best solution.
    If there is a better one, please open an issue and let me know.
    """
    def with_connection(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            self = args[0]
            with sqlite3.connect(self.db_file) as _con:
                _cur = _con.cursor()
                val = func(*args, **kwargs, _con=_con, _cur=_cur)
                _con.commit()
                return val
        return wrapper_decorator


    """
    Deletes all data from the state system.
    """
    @with_connection
    def delete_all(self, _con=None, _cur=None) -> None:
        _cur.execute("DELETE FROM content")

    """
    Rename for backwards compatability with event dictionary.
    Technically this should be depricated.
    """
    def clear(self) -> None:
        self.delete_all()

    """
    Removes an id from the state system.
    """
    @with_connection
    def delete_id(self, id: str, _con=None, _cur=None) -> None:
        _cur.execute("DELETE FROM content WHERE id = ?", (id,))

    """
    Gets the title and path given the id.
    Returns:
        List of (title, path)
    """
    @with_connection
    def get_info(self, id: str, _con=None, _cur=None) -> list:
        _cur.execute("SELECT title, path FROM content WHERE id = ?", (id,))
        result = _cur.fetchone()
        if result == None:
            return ()

        return list(result)

    """
    Gets everything from the database.
    Returns:
        A list of lists in the form (id, path, title). Eg. [(id, path, title), (id, path, title)].
    """
    @with_connection
    def get_all(self, _con=None, _cur=None) -> list:
        _cur.execute("SELECT * FROM content")
        return [list(x) for x in _cur.fetchall()]

    """
    Get everything from the database as a dictionary of id: path title
    Returns:
        A dictionary in the format {ID: {title: "", path: ""}}
    """
    @with_connection
    def get_all_as_dict(self, _con=None, _cur=None) -> dict:
        _cur.execute("SELECT * FROM content")
        result = _cur.fetchall()
        if result == None or len(result) == 0:
            return {}
        return { x[0]: {'title': x[2], 'path': x[1]} for x in result}

    """
    Get all ids in the system.
    Returns:
        A list of ids.
    """
    @with_connection
    def get_all_ids(self, _con=None, _cur=None) -> list:
        _cur.execute("SELECT id FROM content")
        return [x[0] for x in _cur.fetchall()]

    """
    Add content to the state. Title is optional and only for reporting.
    """
    @with_connection
    def add_content(self, id: str, path: str, title: str = None, _con=None, _cur=None) -> None:
        try:
            _cur.execute("INSERT INTO content (id, path, title) VALUES (?, ?, ?)", (id, path, '' if title == None else title))
        except sqlite3.IntegrityError:
            # Duplicate, since its logged we will keep the order one.
            pass

    """
    Returns the number of items inside the state manager.
    """
    def __len__(self) -> int:
        with sqlite3.connect(self.db_file) as _con:
            _cur = _con.cursor()
            _cur.execute("SELECT COUNT(*) FROM content")
            return int(_cur.fetchone()[0])

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

    def _download_id_and_remove_if_success(self, id: str, path: str, state_manager: StateManager) -> dict:
        self.download_id(id, path)
        if id in state_manager.get_all_ids():
            state_manager.delete_id(id)
          
    """
    Select all files for the given id when it has waiting_file_selection
    """
    def _select_files_for_torrent(self, id: str):
        req = requests.post(self._server + "torrents/selectFiles/" + id, data={'files': 'all'}, headers=self._header)
        res = json.loads(req.text)

    """
    Function to check with real debrid to see file status and react accordingly
    """
    def rd_listener(self, state_manager: StateManager) -> bool:
        
        # If there is nothing to watch, why poll RD?
        if len(state_manager) == 0:
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
        seen_ids = {}

        watched_ids = state_manager.get_all_ids()
        
        # For each of the different torrent files we obtained
        for file in res:

            # If the file is being watched, check status
            if file['id'] in watched_ids:
                seen_ids[file['id']] = True

                info = state_manager.get_info(file['id'])

                # If there is no info, then the id isn't in the database.
                # Remove it from the state manager as some how its reporting with an id.
                if info == ():
                    state_manager.delete_id(file['id'])
                    continue

                path = info[1]

                # If its downloaded and ready, process and remove for next cycle. 
                # Otherwise if error log and remove.
                if file['status'] == 'downloaded':
                    self._download_id_and_remove_if_success(file['id'], path, state_manager)
                elif file['status'] == 'magnet_error':
                    self._logger.error("Magnet error on torrent with id: %s, path: %s" 
                        % (file['id'], path))
                    state_manager.delete_id(file['id'])
                    continue
                elif file['status'] == 'virus':
                    self._logger.error("Virus detected on torrent with id: %s, path: %s" 
                        % (file['id'], path))
                    state_manager.delete_id(file['id'])
                    continue
                elif file['status'] == 'error':
                    self._logger.error("Generic error on torrent with id: %s, path: %s" 
                        % (file['id'], path))
                    state_manager.delete_id(file['id'])
                    continue
                elif file['status'] == 'dead':
                    self._logger.error("Dead torrent with id: %s, path: %s" 
                        % (file['id'], path))
                    state_manager.delete_id(file['id'])
                    continue
                elif file['status'] == 'waiting_files_selection':
                    self._select_files_for_torrent(file['id'])
                    state_manager.delete_id(file['id'])
                    continue
        
        # Remove all ids that were not included in the torrents check.
        # I believe this only happens when the torrent is deleted from real-debrid.
        watched_ids = state_manager.get_all_ids()

        for id in watched_ids:
            if id not in seen_ids:
                
                # Same check as above, make sure there is info
                info = state_manager.get_info(id)
                if info == ():
                    state_manager.delete_id(id)
                    self._logger.warning("Torrent failed to be checked with RD (deleted from torrents?) id: %s" 
                        % (id))
                    continue

                path = info[1]
                self._logger.warning("Torrent failed to be checked with RD (deleted from torrents?) id: %s, path: %s" 
                    % (id, path))
                state_manager.delete_id(id)

        return True