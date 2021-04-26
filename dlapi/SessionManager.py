from datetime import date, timedelta
import secrets

# Class representing a user session. Just a struct.
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

    def __str__(self):
        return "IP: %s - Token: %s - Expiry: %s" % (self._ip, self._token, self._expiry)

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