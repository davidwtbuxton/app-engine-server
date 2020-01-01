import io
import os.path
import tempfile
import unittest

from werkzeug import test
from werkzeug import wrappers
import werkzeug

import devserver


class ValidateHandlerConfigTestCase(unittest.TestCase):
    def test_invalid_multiple_types(self):
        handler = {
            'url': '',
            'static_dir': '',
            'script': '',
            'static_files': '',
        }

        err = r'must define exactly 1 of script, static_dir, static_files'

        with self.assertRaisesRegex(ValueError, err):
            devserver.validate_handler_config(handler)

    def test_invalid_missing_url(self):
        handler = {'script': ''}

        err = r'missing "url"'

        with self.assertRaisesRegex(ValueError, err):
            devserver.validate_handler_config(handler)

    def test_valid_script_handler(self):
        handler = {
            'url': '',
            'script': 'auto',
        }

        self.assertIsNone(devserver.validate_handler_config(handler))


class DevserverTestCase(unittest.TestCase):
    def test_page_not_found(self):
        config = [
            {
                'url': '/static',
                'static_dir': 'static',
            },
        ]
        app = devserver.devserver(config=config)
        client = werkzeug.Client(app, werkzeug.Response)
        response = client.get('/')

        self.assertEqual(response.status_code, 404)

    def test_serve_static_dir(self):
        with tempfile.TemporaryDirectory() as static_dir:
            foo_filename = os.path.join(static_dir, 'foo.txt')

            with open(foo_filename, 'w') as fh:
                fh.write('foo!')

            config = [
                {
                    'url': '/static',
                    'static_dir': static_dir,
                },
            ]

            app = devserver.devserver(config=config)
            client = werkzeug.Client(app, werkzeug.Response)
            response = client.get('/static/foo.txt')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.headers['Cache-Control'], 'public')
        self.assertEqual(response.headers['Content-Length'], '4')
        self.assertEqual(response.data, b'foo!')

    def test_serve_static_files(self):
        with tempfile.TemporaryDirectory() as static_dir:
            foo_filename = os.path.join(static_dir, 'foo.txt')

            with open(foo_filename, 'w') as fh:
                fh.write('foo!')

            config = [
                {
                    'url': r'/static/(.*\.txt)$',
                    'static_files': static_dir + r'/\1',
                },
            ]

            app = devserver.devserver(config=config)
            client = werkzeug.Client(app, werkzeug.Response)
            response = client.get('/static/foo.txt')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.headers['Cache-Control'], 'public')
        self.assertEqual(response.headers['Content-Length'], '4')
        self.assertEqual(response.data, b'foo!')


if __name__ == '__main__':
    unittest.main()
