
import myjdapi

class JDownloadManagerException(BaseException):
    pass

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