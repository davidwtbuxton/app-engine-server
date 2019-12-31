"""
Usage:

    # main.py
    import devserver
    import flask

    app = flask.Flask(__name__)

    @app.route('/')
    def home():
        return 'Hell, oh.'

    app = devserver.devserver(app)

Or run from the command line:

    python -m devserver app.yaml
"""
import datetime
import functools
import mimetypes
import os
import re
import typing

import werkzeug
import werkzeug.http
import werkzeug.wsgi


DEFAULT_SERVICE_YAML = 'app.yaml'
DEFAULT_CONTENT_TYPE = 'text/plain'


class App(object):
    def __init__(self, routes):
        self._dispatch = {}

        for pattern, func in routes:
            if isinstance(pattern, str):
                pattern = re.compile(pattern)

            self._dispatch[pattern] = func

    def __call__(self, environ, start_response):
        path_info = werkzeug.wsgi.get_path_info(environ)

        for pattern in self._dispatch:
            match = pattern.search(path_info)

            if match:
                groups = match.groups()
                handler = self._dispatch[pattern]

                return handler(environ, start_response)

        return self.not_found(environ, start_response)

    @classmethod
    def static_dir(cls, url_pattern, static_dir, environ, start_response):
        path_info = werkzeug.wsgi.get_path_info(environ)

        try:
            # If it is a match we get a pair of ['', '/filename.txt'].
             _, remainder = url_pattern.split(path_info)
        except ValueError:
            return cls.not_found(environ, start_response)

        remainder = remainder.lstrip('/')
        filename = os.path.join(static_dir, remainder)
        content_type = mimetypes.guess_type(filename) or DEFAULT_CONTENT_TYPE
        mtime = datetime.utcfromtimestamp(os.path.getmtime(filename))
        size = int(os.path.getsize(filename))

        headers = [
            ('Date', werkzeug.http.http_date()),
            ('Content-Type', content_type),
            ('Content-Length', str(size)),
            ('Last-Modified', werkzeug.http.http_date(mtime)),
            ('Cache-Control', 'public'),
        ]

        fh = open(filename, 'rb')
        start_response('200 OK', headers)
        response = werkzeug.wsgi.wrap_file(environ, fh)

        return response

    @classmethod
    def not_found(cls, environ, start_response):
        response = werkzeug.Response('Not Found', status=404)

        return response(environ, start_response)


def is_gae(env: dict) -> bool:
    """True if the code is running on App Engine."""
    return env.get('GAE_ENV') == 'standard'


def find_filename(filename: str, parent_dir: str) -> typing.Optional[str]:
    """Returns the full path to the named file in the directory or one if its
    parent directories, or None of no file can be found.
    """
    while True:
        candidate = os.path.join(parent_dir, filename)
        if os.path.exists(candidate):
            return candidate

        next_parent_dir = os.path.dirname(parent_dir)
        if next_parent_dir == parent_dir:
            break
        else:
            parent_dir = next_parent_dir


def validate_handler_config(d: dict) -> None:
    """Raises ValueError if the config makes no sense. Else returns None."""
    if 'url' not in d:
        raise ValueError('Invalid handler, missing "url"')

    defined = set(d)
    permitted = set(['script', 'static_dir', 'static_files'])
    num_valid = len(defined & permitted)

    if num_valid != 1:
        choices = ', '.join(sorted(permitted))
        raise ValueError('Invalid handler, must define exactly 1 of %s' % choices)


def read_handler_config(config_filename: str) -> typing.Iterable:
    cwd = os.getcwd()
    yaml_filename = find_filename(config_filename, cwd)

    with open(yaml_filename) as fh:
        config = yaml.safe_load(fh)

    for conf in config['handlers']:
        validate_handler_config(conf)
        yield conf


def devserver(app=App.not_found, config=None, config_filename=DEFAULT_SERVICE_YAML):
    """Adds handlers for static routes defined in app.yaml to a WSGI app.

    For each handler in app.yaml which defines a static_file or static_dir
    handler, a route is added to the wrapper WSGI app to serve the appropriate
    files from the filesystem.

    All other routes are handled by the wrapped ``app``.

    This is intended as a helper for local development of App Engine
    applications, mimicing how static files will be handled in production. When
    deployed to App Engine, this helper returns the app (noop).
    """
    # We are deployed to App Engine, do nothing.
    if is_gae(os.environ):
        return app

    if config is None:
        config = read_handler_config(config_filename)

    routes = []

    for handler_config in config:

        if 'script' in handler_config:
            handler = app
            pattern = r'^' + handler_config['url']

        elif 'static_dir' in handler_config:
            pattern = re.compile(r'^' + handler_config['url'] + r'(.*)')
            static_dir = handler_config['static_dir']
            handler = functools.partial(App.static_dir, pattern, static_dir)

        elif 'static_files' in handler_config:
            handler = App.static_dir
            pattern = r'^' + handler_config['url']

        routes.append((pattern, handler))

    wrapper = App(routes=routes)

    return wrapper
