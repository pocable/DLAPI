
from datetime import date, timedelta
import secrets
from dlapi.utilclasses import Session
from myjdapi.myjdapi import Jddevice, Myjdapi

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
    NOTE: This function can be slow with a massive load of people
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

        # Check if the ip is in the sessions, then iterate over all sessions at the house
        # until either it finds a valid session or it returns False
        if ip in self.ip_sessions:
            sessions = self.ip_sessions[ip]
            for session in sessions:
                if session.get_token() == token and session.get_ip() == ip:
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