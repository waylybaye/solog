"""
solog, yet another blog application

NO database required, all file based.
"""
from collections import namedtuple
from datetime import datetime
import json
import os
import re
import sqlite3
import uuid
from dateutil import parser
from dropbox import session, client
import markdown
from markdown.extensions.headerid import slugify
import mustache
import unicodedata
from bottle import route, run, Bottle, static_file, request, redirect, response, HTTPResponse

app = Bottle()
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
CONF_ROOT = os.path.join(PROJECT_ROOT, "conf")
CACHE_ROOT = CONF_ROOT
SETTINGS_ROOT = CONF_ROOT

TEMPLATES_ROOT = os.path.join(PROJECT_ROOT, "templates")
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

SETTINGS_FILE = os.path.join(SETTINGS_ROOT, "settings.json")
CACHE_DB_FILE = os.path.join(CACHE_ROOT, "data.db")


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
    auth_url = sess.build_authorize_url(request_token, callback)
    # response.set_cookie('request_token', '&'.join([request_token.key, request_token.secret]))

    resp = HTTPResponse("", status=302, Location=auth_url)
    resp.set_cookie('request_token', '&'.join([request_token.key, request_token.secret]))
    return resp


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

    # save session
    token = str(uuid.uuid4())
    storage.set('session', token)
    storage.write()

    response.set_cookie('session', token, max_age=3600*24*10)
    redirect("/dropbox/sync?session=" + token)


@app.route('/dropbox/sync')
def dropbox_sync():
    """
    Sync posts and settings with Dropbox

    * List Dropbox blog folder and convert them to html.
    * Save local settings file to Dropbox
    """
    conn = sqlite3.connect(CACHE_DB_FILE)
    storage = SettingStorage(SETTINGS_FILE)

    consumer_key = storage.get('dropbox:consumer_key')
    consumer_secret = storage.get('dropbox:consumer_secret')
    access_token_key = storage.get('dropbox:access_token_key')
    access_token_secret = storage.get('dropbox:access_token_secret')

    session_token = storage.get('session')
    if not request.get_cookie('session') == session_token and not request.GET.get('session') == session_token:
        return "Oops, who are you?"

    if not consumer_key or not consumer_secret:
        return "Oops, did you install me?"

    if not access_token_key or not access_token_secret:
        return "Oops, did you authenticate?"

    sess = session.DropboxSession(consumer_key, consumer_secret, 'app_folder')
    sess.set_token(access_token_key, access_token_secret)

    api = client.DropboxClient(sess)
    metas = api.metadata('/')

    new_or_updated_files = []

    for content in metas['contents']:
        name = content['path']
        modified = parser.parse(content['modified'])

        post = db_get_post(conn, filename=name)
        if not post:
            new_or_updated_files.append(name)
            continue

        if post.last_update < modified:
            new_or_updated_files.append(name)

    print "update ", new_or_updated_files
    for name in new_or_updated_files:
        update_post(request, api, name)

    return redirect("/")


def update_post(request, api, path):
    """
    Update or create a post from Dropbox file
    Supported markdown Meta:
        Title: Post title
        Slug: url slug. default slugify(title), filename
        Date: post created date
        Published: not publish this post if Published is false
    """
    parent_dir, name = os.path.split(path)
    conn = sqlite3.connect(CACHE_DB_FILE)

    post = db_get_post(conn, filename=path)
    if not post:
        post = Post(filename=path)

    f, metadata = api.get_file_and_metadata(path)
    content = f.read()

    last_modified = parser.parse(metadata['modified'])

    extensions = ['meta', 'fenced_code']
    md = markdown.Markdown(extensions=extensions)

    html = md.convert(content.decode('utf8'))

    file_name = os.path.splitext(name)[0]
    meta = md.Meta

    default_slug = unicodedata.normalize('NFKD', file_name).encode('ascii', 'ignore').decode('ascii')
    default_slug = re.sub('[^\w\s-]', '', default_slug).strip().lower()
    default_slug = re.sub('[-\s]+', '-', default_slug)

    title = meta.get('title', [file_name])[0]
    slug = meta.get('slug', [default_slug])[0]
    not_published = 'published' in meta and meta.get('published')[0].lower() == 'false'
    created_date = parser.parse(meta.get('date')[0]) if 'date' in meta else datetime.now()

    # if 'date' in meta:
    #     post.created_at = created_date
    # else:
    #     if not post.created_at:
    #         post.created_at = last_modified

    post.last_update = last_modified
    post.title = title
    post.slug = slug
    post.html = html
    post.is_published = not not_published
    db_save_post(conn, post)


@app.route('/post/<slug:re:[\w-]+>')
def view_post(slug):
    conn = sqlite3.connect(CACHE_DB_FILE)
    post = db_get_post(conn, slug=slug)
    context = {
        'post': post,
    }

    return render_template('post.html', context)


# Post = namedtuple('Post', 'id title slug content last_update')
class Post(object):
    def __init__(self, id=None, title=None, slug=None, content=None, filename=None, last_update=None):
        self.id = id
        self.title = title
        self.slug = slug
        self.content = content
        self.last_update = last_update
        self.filename = filename


def db_initialize(conn):
    # conn = sqlite3.connect(CACHE_DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS posts
                (id integer primary key, title text, slug text,
                content text, last_update timestamp,
                filename text)''')


def db_save_post(conn, post):
    cursor = conn.cursor()
    if post.id:
        cursor.execute(
            '''UPDATE posts SET title=:title, slug=:slug,
            content=:content, last_update=:last_update,
            filename=:filename''',
            {
                'title': post.title,
                'slug': post.slug,
                'filename': post.filename,
                'content': post.content,
                'last_update': post.last_update})
    else:
        cursor.execute(
            '''INSERT INTO posts(title, slug, content, last_update)
                       VALUES(?, ?, ?, ?)''',
            [post.title, post.slug, post.content, post.last_update])
    conn.commit()


def db_list_post(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id,title,slug,content,last_update FROM posts')
    results = cursor.fetchall()
    return [Post(*result) for result in results]


def db_get_post(conn, **kwargs):
    cursor = conn.cursor()
    query = " and ".join(['%s=:%s' % (key, key) for key in kwargs.keys()])
    cursor.execute('SELECT id,title,slug,content,last_update FROM posts WHERE %s' % query, kwargs)
    result = cursor.fetchone()
    if result:
        return Post(*result)


def install():
    """
    initialize solog application
    """
    if request.method == 'POST':
        dirs = [CONF_ROOT, SETTINGS_ROOT, CACHE_ROOT]
        for dir in dirs:
            if not os.path.exists(dir):
                os.mkdir(dir)

        # let's trust the POST data
        # assume the data has been validated by javascript
        consumer_key = request.POST.get('consumer_key')
        consumer_secret = request.POST.get('consumer_secret')

        storage = SettingStorage(SETTINGS_FILE)
        storage.set('dropbox:consumer_key', consumer_key)
        storage.set('dropbox:consumer_secret', consumer_secret)
        storage.write()

        # Create tables
        conn = sqlite3.connect(CACHE_DB_FILE)
        db_initialize(conn)

        # redirect to dropbox auth
        return redirect('/dropbox/auth')

    return render_template("install.html", {})


@app.route('/', method=['GET', 'POST'])
def index():
    """
    Blog index page
    """
    if not _is_installed():
        return install()

    conn = sqlite3.connect(CACHE_DB_FILE)
    context = {
        'posts': db_list_post(conn)
    }
    return render_template('index.html', context)


if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)
