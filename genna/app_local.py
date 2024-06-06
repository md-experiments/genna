
from threading import Lock
from werkzeug.wsgi import pop_path_info, peek_path_info
from werkzeug.serving import run_simple
from anna.app import app

from flask import Flask, redirect



class AppConfig():
    NAV_BAR = [
        {'name': 'Home', 'link': '/anna/'},
    ]
    PREFIX = 'anna'
    PROJECT = 'anna'
    INPUT_PATH = '../endeavor/text_structure_extract/data/datasets'
    CONFIG_FILE_PATH = './config.yaml'
    ANNOTATIONS_PATH = '../endeavor/text_structure_extract/data'
    ANNOTATIONS_LATEST_PATH = '../endeavor/text_structure_extract/data/annotations_latest'
    WORKFLOW_NEXT_BUTTON_URL = './anna'
    WORKFLOW_HEADER = 'Anna'

class AppConfig():
    NAV_BAR = [
        {'name': 'Home', 'link': '/anna/'},
    ]
    PREFIX = 'anna'
    PROJECT = 'anna'
    INPUT_PATH = './data/datasets'
    CONFIG_FILE_PATH = './config.yaml'
    ANNOTATIONS_PATH = './data'
    ANNOTATIONS_LATEST_PATH = './data/annotations_latest'
    WORKFLOW_NEXT_BUTTON_URL = './anna'
    WORKFLOW_HEADER = 'Anna'

default_app = Flask(__name__)
default_app.debug = True

@default_app.route('/')
def initial():
    return redirect('/anna/')

class PathDispatcher(object):

    def __init__(self, default_app, create_app):
        self.default_app = default_app
        self.create_app = create_app
        self.lock = Lock()
        self.instances = {}

    def get_application(self, prefix):
        with self.lock:
            app = self.instances.get(prefix)
            if app is None:
                app = self.create_app(prefix)
                if app is not None:
                    self.instances[prefix] = app
            return app

    def __call__(self, environ, start_response):
        app = self.get_application(peek_path_info(environ))
        if app is not None:
            pop_path_info(environ)
        else:
            app = self.default_app
        return app(environ, start_response)

get_user_for_prefix ={
    'anna':'__main__.AppConfig',
}

def create_app(config_filename):
    app.config.from_object(config_filename)
    return app

def make_app(prefix):
    user = get_user_for_prefix.get(prefix,None)
    if user is not None:
        return create_app(user)

application = PathDispatcher(default_app, make_app)


if __name__ == '__main__':
    # python -m anna.app_local (invoke as module)
    run_simple('localhost', 5001, application,
               use_reloader=True, use_debugger=True, use_evalex=True)
