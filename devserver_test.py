import io
import os.path
import shutil
import tempfile
import unittest

from werkzeug import test
from werkzeug import wrappers
import werkzeug

import devserver


app_yaml = io.StringIO("""
runtime: python37

handlers:

  - url: /
    static_dir: dist

""")
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
    def test_devserver_page_not_found(self):
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

    def test_devserver_serve_file(self):
        static_dir = tempfile.mkdtemp()
        foo_filename = os.path.join(static_dir, 'foo.txt')

        with open(foo_filename, 'w') as fh:
            fh.write('foo!')

        config = [
            {
                'url': '/static',
                'static_dir': static_dir,
            },
        ]

        try:
            app = devserver.devserver(config=config)
            client = werkzeug.Client(app, werkzeug.Response)
            response = client.get('/static/foo.txt')
        finally:
            shutil.rmtree(static_dir)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers, {})



if __name__ == '__main__':
    unittest.main()
