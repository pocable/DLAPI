from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from dlapi.managers import SessionManager, RDManager, JDownloadManager, StateManager
import os
from flask_cors import CORS
from flask_apscheduler import APScheduler

app = Flask(__name__)
CORS(app)

# Logging
logger = logging.getLogger('gunicorn.error')
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# Limiting
limiter = Limiter(app, key_func=get_remote_address)

# Managers
session_manager = SessionManager(int(os.environ['SESSION_EXPIRY_DAYS']) if 'SESSION_EXPIRY_DAYS' in os.environ else 1)
jdownload_manager = JDownloadManager(os.environ['JD_USER'], os.environ['JD_PASS'], os.environ['JD_DEVICE'], logger)
real_debrid_manager = RDManager(os.environ['RD_KEY'], logger, jdownload_manager)
state_manager = StateManager("./dlconfig/state.db")

# Configuration object for scheduling update
class Config(object):
    JOBS = [
        {
            'id': 'RDListener',
            'func': real_debrid_manager.rd_listener,
            'args': (state_manager,),
            'trigger': 'interval',
            'seconds': 15
        },
        {
            'id': 'SessionManager',
            'func': session_manager.remove_expired_sessions,
            'args': (),
            'trigger': 'interval',
            'seconds': 60 * 60
        }
    ]

    SCHEDULER_API_ENABLED = True

# Scheduling
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


from dlapi import views