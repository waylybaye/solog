import json
import unittest
from views import SettingStorage
import tempfile


class StorageTest(unittest.TestCase):
    def test_settings_storage(self):
        path = tempfile.mktemp('.json')
        storage = SettingStorage(path)
        title = u'Hello solog'

        storage.set('blog:title', title)
        self.assertEqual(storage.get('blog:title'), title)
        self.assertTrue(json.load(open(path, 'r')).keys(), ['blog:title'])

        self.assertEqual(storage.get('blog:none', 'default'), 'default')

        storage.set('dropbox:access_token', 'access_token')
        self.assertTrue(json.load(open(path, 'r')).keys(), ['blog:title', 'dropbox:access_token'])


if __name__ == '__main__':
    unittest.main()
