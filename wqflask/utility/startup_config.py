
from wqflask import app

from utility.configuration import show_settings
from utility.configuration import get_setting_int
from utility.configuration import get_setting
from utility.configuration import get_setting_bool


BLUE = '\033[94m'
GREEN = '\033[92m'
BOLD = '\033[1m'
ENDC = '\033[0m'


def app_config(app):
    app.config['SESSION_TYPE'] = app.config.get('SESSION_TYPE', 'filesystem')
    if not app.config.get('SECRET_KEY'):
        import os
        app.config['SECRET_KEY'] = str(os.urandom(24))
    mode = get_setting(app, "WEBSERVER_MODE")
    if mode in ["DEV", "DEBUG"]:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        if mode == "DEBUG":
            app.debug = True

    print("==========================================")
    show_settings(app)

    port = get_setting_int(app, "SERVER_PORT")

    if get_setting_bool(app, "USE_GN_SERVER"):
        print(f"GN2 API server URL is [{BLUE}GN_SERVER_URL{ENDC}]")
        import requests
        page = requests.get(get_setting(app, "GN_SERVER_URL"))
        if page.status_code != 200:
            raise Exception("API server not found!")
    print(f"GN2 is running. Visit {BLUE}"
          f"[http://localhost:{str(port)}/{ENDC}]"
          f"({get_setting(app, 'WEBSERVER_URL')})")
