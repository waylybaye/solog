"""
solog, yet another blog application

NO database required, all file based.
"""
import json
import os
from dropbox import session
import mustache
from bottle import route, run, Bottle, static_file, request, redirect

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

    def save(self):
        pass


class SettingStorage(Storage):
    def __init__(self, path):
        self.path = path
        if os.path.isfile(path):
            fp = open(path, 'rb')
            self.cache = json.load(fp, encoding='utf8')
            fp.close()
        else:
            self.cache = {}

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, key, value):
        self.cache[key] = value

    def write(self):
        fp = open(self.path, 'wb')
        json.dump(self.cache, fp, indent=2)
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
    storage = SettingStorage(SETTINGS_FILE)
    consumer_key = storage.get('dropbox:consumer_key')
    consumer_secret = storage.get('dropbox:consumer_secret')
    sess = session.DropboxSession(consumer_key, consumer_secret, 'app_folder')

    request_token = sess.obtain_request_token()

    callback = "%s://%s/dropbox/auth/callback" % (request.urlparts.scheme, request.urlparts.netloc)
    http_response = redirect(callback)
    http_response.set_cookie('request_token', '&'.join([request_token.key, request_token.secret]))
    return http_response


@app.route('/dropbox/auth/callback')
def dropbox_callback():
    """
    Dropbox oauth callback
    """
    storage = SettingStorage(SETTINGS_FILE)
    request_token = request.get_cookie('request_token')
    if not request_token:
        return "Oops, something is wrong ..."

    consumer_key = storage.get('dropbox:consumer_key')
    consumer_secret = storage.get('dropbox:consumer_secret')
    sess = session.DropboxSession(consumer_key, consumer_secret, 'app_folder')
    request_token = session.OAuthToken(*request_token.split('&'))
    access_token = sess.obtain_access_token(request_token)

    storage.set('dropbox:access_token_key', access_token.key)
    storage.set('dropbox:access_token_secret', access_token.secret)
    storage.write()

    return redirect("/dropbox/sync")


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
        # let's trust the POST data
        # assume the data has been validated by javascript
        consumer_key = request.POST.get('consumer_key')
        consumer_secret = request.POST.get('consumer_secret')

        storage = SettingStorage(SETTINGS_FILE)
        storage.set('dropbox:consumer_key', consumer_key)
        storage.set('dropbox:consumer_secret', consumer_secret)
        storage.write()

        # redirect to dropbox auth
        return redirect('/dropbox/auth')

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
