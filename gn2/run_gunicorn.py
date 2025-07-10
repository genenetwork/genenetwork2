# Run with gunicorn, see ./bin/genenetwork2 for an example
#
# Run standalone with
#
#   ./bin/genenetwork2 ./gn2/default_settings.py -c run_gunicorn.py

# from flask import Flask
# application = Flask(__name__)
from pathlib import Path
from werkzeug.middleware.profiler import ProfilerMiddleware

print("===> Starting up Gunicorn process")

from gn2.gn2_main import app
from gn2.utility.startup_config import app_config

app_config()


@app.route("/gunicorn")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

if app.config.get("RUN_UNDER_PROFILER"):
    profiler_settings = app.config.get(
        "PROFILER_SETTINGS", {
            "profile_dir": Path("instance/profiler")
        }
    )
    profiler_dir = Path(profiler_settings["profile_dir"])
    profiler_dir.mkdir(parents=True, exist_ok=True)
    app = ProfilerMiddleware(app, **profiler_settings)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
