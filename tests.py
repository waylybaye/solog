from sqlite3 import IntegrityError
from collections import namedtuple
from datetime import datetime
import json
import os
import sqlite3
import mock
import unittest
from bottle import HTTPResponse, BaseRequest
from views import SettingStorage, db_initialize, db_save_post, db_get_post, db_list_post, Post, db_ensure_unique
import tempfile
import views


class StorageTest(unittest.TestCase):
    def test_settings_storage(self):
        path = tempfile.mktemp('.json')
        storage = SettingStorage(path)
        title = u'Hello solog'

        storage.set('test:blog:title', title)
        storage.write()

        self.assertEqual(storage.get('test:blog:title'), title)

        fp = open(path, 'r')
        self.assertTrue(json.load(fp).keys(), ['blog:title'])
        fp.close()

        self.assertEqual(storage.get('blog:none', 'default'), 'default')

        storage.set('test:dropbox:access_token', 'access_token')
        storage.write()
        self.assertEqual(json.load(open(path, 'r')).keys(), ['test:blog:title', 'test:dropbox:access_token'])


class DbTest(unittest.TestCase):
    def test_db(self):
        conn = sqlite3.connect(':memory:')
        db_initialize(conn)
        results = conn.execute('SELECT name FROM sqlite_master WHERE type = "table"').fetchall()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'posts')

        post = views.Post(id=None, title='Hello', content="<h1>Good<h1>", slug="hello-world", last_update=datetime.now())
        db_save_post(conn, post)

        saved_post = db_get_post(conn, slug='hello-world')
        self.assertEqual(post.title, 'Hello')
        self.assertEqual(type(saved_post.last_update), datetime)

        # Save twice
        self.assertEqual(len(db_list_post(conn)), 1)
        self.assertRaises(IntegrityError, lambda: db_save_post(conn, post))
        post.slug = db_ensure_unique(conn, 'slug', post.slug)
        db_save_post(conn, post)
        self.assertEqual(len(db_list_post(conn)), 2)
        self.assertEqual(post.slug, "hello-world-2")

        saved_post.title = "New Title"
        db_save_post(conn, saved_post)
        self.assertEqual(len(db_list_post(conn)), 2)
        self.assertEqual(db_get_post(conn, slug='hello-world').title, "New Title")

        # test db_list_post with filters
        self.assertEqual(len(db_list_post(conn, is_published=1)), 0)

        saved_post.is_published = True
        db_save_post(conn, saved_post)
        self.assertEqual(len(db_list_post(conn)), 2)
        self.assertEqual(len(db_list_post(conn, is_published=1)), 1)

        # test db_list_post order by
        rs = db_list_post(conn, order_by="id")
        self.assertEqual(rs[0].id, 1)
        rs = db_list_post(conn, order_by="-id")
        self.assertEqual(rs[0].id, 2)


class AppTest(unittest.TestCase):
    cache_file = tempfile.mktemp(".db")

    def test_post_detail(self):
        with mock.patch('views.CACHE_DB_FILE', self.cache_file):
            conn = sqlite3.connect(self.cache_file)
            post = Post(title="Hello", slug="hello", content="<h1>Hello</h1>", last_update=datetime.now())
            db_initialize(conn)
            db_save_post(conn, post)
            response = views.view_post(post.slug)

            self.assertTrue(post.title in response)
            self.assertTrue(post.content in response)


class DropboxTest(unittest.TestCase):
    def setUp(self):
        tmp_file = tempfile.mktemp('.json')
        storage = SettingStorage(tmp_file)
        storage.set('dropbox:consumer_key', 'consumer key')
        storage.set('dropbox:consumer_secret', 'consumer secret')
        self.settings_file = tmp_file

    def tearDown(self):
        os.remove(self.settings_file)

    @mock.patch('dropbox.session.DropboxSession')
    def test_auth(self, MockSession):
        with mock.patch('views.SETTINGS_FILE', self.settings_file):
            AccessToken = namedtuple('AccessToken', "key secret")
            sess = MockSession()
            sess.obtain_request_token.return_value = AccessToken(key="key", secret="secret")

            http_response = views.dropbox_auth()
            self.assertEqual(http_response.status_code, 302)

            self.assertTrue(sess.obtain_request_token.called)
            self.assertEqual(views.dropbox_callback(), 'Oops, something is wrong ...')

            with mock.patch.object(BaseRequest, 'get_cookie', lambda *args: "key&secret"):
                sess.obtain_access_token.return_value = AccessToken(key="key", secret="secret")

                # should redirect to /dropbox/sync
                self.assertRaises(HTTPResponse, lambda: views.dropbox_callback())
                self.assertTrue(sess.obtain_access_token.called)
                storage = SettingStorage(self.settings_file)
                self.assertEqual(storage.get('dropbox:access_token_secret'), 'secret')
                self.assertEqual(storage.get('dropbox:access_token_key'), 'key')


if __name__ == '__main__':
    unittest.main()
