"""
solog, yet another blog application

NO database required, all file based.
"""
import json
import os
import mustache
from bottle import route, run, Bottle, static_file, request

app = Bottle()
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
CACHE_FOLDER = os.path.join(PROJECT_ROOT, "cache")
SETTINGS_ROOT = os.path.join(PROJECT_ROOT, "settings")
TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "templates")
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

SETTINGS_FILE = os.path.join(SETTINGS_ROOT, "settings.json")


def _is_installed():
    return os.path.exists(SETTINGS_FILE)


def render_template(name, context):
    template = open(os.path.join(TEMPLATES_ROOT, name), 'r').read()
    return mustache.render(template, context)


class Storage(object):
    """
    A storage to save cached html files and user settings

    >>> storage = Storage()
    >>> blog_title = storage.get('blog:title')
    >>> access_token = storage.get('dropbox:access-token')
    """
    def collect_files(self):
        """
        Return list of `file` like objects,
        which will be saved to Dropbox to keep sync
        """

    def set(self, key, value):
        pass

    def get(self, key):
        pass


class SettingStorage(Storage):
    def __init__(self, path):
        self.path = path

    def get(self, key, default=None):
        fp = open(self.path, 'r')
        value = json.load(fp, encoding='utf8').get(key, default)
        fp.close()
        return value

    def set(self, key, value):
        fp = open(self.path, 'w+')
        try:
            object = json.load(fp, encoding='utf8')
        except ValueError:
            object = {}
        object[key] = value
        json.dump(object, fp)
        fp.close()


@app.route('/static/<filename:path>')
def static_files(filename):
    """
    Serving static files

    .. note:
        only for development usage
    """
    return static_file(filename, root=STATIC_ROOT)


@app.route('/dropbox/auth')
def dropbox_auth():
    """
    Get Dropbox oatuh tokens
    """
    return ""


@app.route('/dropbox/sync')
def dropbox_sync():
    """
    Sync posts and settings with Dropbox

    * List Dropbox blog folder and convert them to html.
    * Save local settings file to Dropbox
    """

@app.route('/post/<slug:re:[\w-]+>')
def view_post(slug):
    pass


def install():
    """
    initialize solog application
    """
    if request.method == 'POST':
        return "POST"

    request.cookies.get()
    context = {}
    return render_template("install.html", {})


@app.route('/')
def index():
    """
    Blog index page
    """
    if not _is_installed():
        return install()

    return mustache.render()


if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)
