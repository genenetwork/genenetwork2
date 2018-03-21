
from wqflask import app
from utility.tools import WEBSERVER_MODE, show_settings, get_setting_int, get_setting, get_setting_bool

import utility.logger
logger = utility.logger.getLogger(__name__ )

BLUE  = '\033[94m'
GREEN = '\033[92m'
BOLD  = '\033[1m'
ENDC  = '\033[0m'

def app_config():
    app.config['SESSION_TYPE'] = 'filesystem'
    if not app.config.get('SECRET_KEY'):
        import os
        app.config['SECRET_KEY'] = str(os.urandom(24))

    mode = WEBSERVER_MODE
    if mode == "DEV" or mode == "DEBUG":
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        # if mode == "DEBUG":
        #     app.config['EXPLAIN_TEMPLATE_LOADING'] = True <--- use overriding app param instead
    print("==========================================")
    show_settings()

    port = get_setting_int("SERVER_PORT")

    if get_setting_bool("USE_GN_SERVER"):
        print("GN2 API server URL is ["+BLUE+get_setting("GN_SERVER_URL")+ENDC+"]")
        import requests
        page = requests.get(get_setting("GN_SERVER_URL"))
        if page.status_code != 200:
            raise Exception("API server not found!")

    import utility.elasticsearch_tools as es
    es.test_elasticsearch_connection()

    print("GN2 is running. Visit %s[http://localhost:%s/%s](%s)" % (BLUE,str(port),ENDC,get_setting("WEBSERVER_URL")))
