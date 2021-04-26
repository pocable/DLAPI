
import myjdapi
from datetime import date, timedelta
import secrets
from dlapi.utilclasses import Session

# Controller for JDownloader
class JDownloadManager():
    def __init__(self, username, password, device_name):
        self.username = username
        self.password = password
        self.device_name = device_name
        self._initialize_session()

    def download(self, urls, path):
        # Check to see if we are connected, if not try to reconnect, and at worse connect from the start
        self._restart_session()
        return self.device.linkgrabber.add_links([{'autostart': True, 'links': '\n'.join(urls), 'destinationFolder': path + "", "overwritePackagizerRules": True}])

    def get_device(self):
        return self.device

    def get_jd(self):
        return self.jd

    """
    Refresh a session depending on if it is connected or not
    """
    def _restart_session(self):
        if self.jd.is_connected():
            self.jd.reconnect()
        else:
            self.jd.connect(self.username, self.password)
            self.jd.update_devices()
            self.device = self.jd.get_device(self.device_name)

    """
    Starts a session with JDownloader. Called on construction of this class.
    """
    def _initialize_session(self):
        jd = myjdapi.Myjdapi()
        jd.set_app_key("DLAPI")
        jd.connect(self.username, self.password)
        jd.update_devices()
        device = jd.get_device(self.device_name)
        self.jd = jd
        self.device = device
        return jd, device

# Class to handle the management of user sessions with the application.
class SessionManager():
    def __init__(self, expiry_days):
        self.expiry_days = expiry_days
        self.ip_sessions = {}

    # Close a session
    def close_session(ip, token):
        if ip in self.ip_sessions:
            for session in self.ip_sessions[ip]:
                if session.get_token() == token:
                    self.ip_sessions[ip].remove(session)

            # If there are no remaining sessions at the ip, remove it.
            if len(self.ip_sessions[ip]) == 0:
                del self.ip_sessions[ip]

    # Check for expired sessions and remove them from the session list.
    # NOTE: This function can be slow with a massive load of people.
    def remove_expired_sessions(self):
        current_time = date.today()
        for ip in self.ip_sessions:

            # For each session in the ip, validate its time.
            for session in self.ip_sessions[ip]:
                if session.get_expiry() < current_time:
                    self.ip_sessions[ip].remove(session)

            # If there are no remaining sessions at the ip, remove it.
            if len(self.ip_sessions[ip]) == 0:
                del self.ip_sessions[ip]

    # Authenticate the user given a token and their IP.
    def authenticate_user(self, token, ip):

        # Check if the ip is in the sessions, then iterate over all sessions at the house
        # until either it finds a valid session or it returns False
        if ip in self.ip_sessions:
            sessions = ip_sessions[ip]
            for session in sessions:
                if session.get_token() == token and session.get_ip() == ip:
                    return True
        
        return False

    # Create a session for the given IP
    def create_session(self, ip):
        token = secrets.token_urlsafe()
        s = Session(ip, token, date.today() + timedelta(days=self.expiry_days))
        if ip in self.ip_sessions:
            self.ip_sessions[ip].append(s)
        else:
            self.ip_sessions[ip] = [s]

        return token

    # Get the internal dictionary of all of the sessions
    def get_sessions(self):
        return self.ip_sessions

    # Manual way to add sessions, mainly will be used for testing.
    def _add_session(self, ip, session):
        if ip in self.ip_sessions:
            self.ip_sessions[ip].append(session)
        else:
            self.ip_sessions[ip] = [session]