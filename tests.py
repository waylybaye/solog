from collections import namedtuple
import json
import os
import mock
import unittest
from bottle import HTTPResponse, BaseRequest
from views import SettingStorage
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
            self.assertRaises(HTTPResponse, lambda: views.dropbox_auth())

            sess = MockSession()

            self.assertTrue(sess.obtain_request_token.called)
            self.assertEqual(views.dropbox_callback(), 'Oops, something is wrong ...')

            with mock.patch.object(BaseRequest, 'get_cookie', lambda *args: "key&secret"):
                AccessToken = namedtuple('AccessToken', "key secret")
                # mock = mock.MagicMock(return_value=AccessToken(key="key", secret="secret"))
                sess.obtain_access_token.return_value = AccessToken(key="key", secret="secret")

                # should redirect to /dropbox/sync
                self.assertRaises(HTTPResponse, lambda: views.dropbox_callback())
                self.assertTrue(sess.obtain_access_token.called)
                storage = SettingStorage(self.settings_file)
                self.assertEqual(storage.get('dropbox:access_token_secret'), 'secret')
                self.assertEqual(storage.get('dropbox:access_token_key'), 'key')


if __name__ == '__main__':
    unittest.main()
