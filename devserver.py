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
import os
import typing


DEFAULT_SERVICE_YAML = 'app.yaml'


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


def check_handler(d: dict) -> None:
    """Raises ValueError if the config makes no sense. Else returns None."""

def make_handler(handler_dict: dict):
    """Convert an app.yaml handler to a WSGI route handler?"""
    # - script: auto then it's a Python handler.
    # - static_files: .* then it's a static handler, serving upload:
    # - static_dir: .* then it's a static handler, serving the directory
    check_handler(handler_dict)

def read_static_handlers(config_filename) -> list:
    cwd = os.getcwd()
    yaml_filename = find_filename(config_filename, cwd)

    with open(yaml_filename) as fh:
        config = yaml.safe_load(fh)

    for handler in config['handlers']:
        make_handler(handler)


def new_service(config_filename):
    handlers = read_static_handlers(config_filename)

    return


def devserver(app):
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

    server = new_service(DEFAULT_SERVICE_YAML)
    wrapper = server(app)

    return wrapper
