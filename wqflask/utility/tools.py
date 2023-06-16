# Tools/paths finder resolves external paths from settings and/or environment
# variables
import os

from .configuration import (
    mk_dir,
    tempdir,
    valid_bin,
    valid_file,
    valid_path,
    assert_bin,
    assert_dir,
    assert_file,
    get_setting,
    get_setting_int,
    get_setting_bool,
    assert_writable_dir)

def js_path(app, module=None):
    """
    Find the JS module in the two paths
    """
    try_gn = get_setting(app, "JS_GN_PATH") + "/" + module
    if valid_path(try_gn):
        return try_gn
    try_guix = get_setting(app, "JS_GUIX_PATH") + "/" + module
    if valid_path(try_guix):
        return try_guix
    raise "No JS path found for " + module + \
        " (if not in Guix check JS_GN_PATH)"

def reaper_command(app, guess=None):
    return get_setting(app, "REAPER_COMMAND", guess)

def gemma_command(app, guess=None):
    return assert_bin(get_setting(app, "GEMMA_COMMAND", guess))

def gemma_wrapper_command(app, guess=None):
    return assert_bin(get_setting(app, "GEMMA_WRAPPER_COMMAND", guess))

def plink_command(app, guess=None):
    return assert_bin(get_setting(app, "PLINK_COMMAND", guess))

def set_mandatory_settings(app):
    """Set up the mandatory settings."""
    ## Setup profile dependent settings: Remove these eventually ##
    GN2_PROFILE = get_setting(app, "GN2_PROFILE", os.environ.get("GN2_PROFILE"))
    app.config["GN2_PROFILE"] = GN2_PROFILE
    app.config["JS_GUIX_PATH"] = get_setting(
        app,
        "JS_GUIX_PATH",
        f"{GN2_PROFILE}/share/genenetwork2/javascript")
    app.config["REAPER_COMMAND"] = reaper_command(app)
    app.config["GEMMA_COMMAND"] = gemma_command(app, f"{GN2_PROFILE}/bin/gemma")
    assert(app.config["GEMMA_COMMAND"] is not None)
    app.config["PLINK_COMMAND"] = plink_command(
        app, f"{GN2_PROFILE}/bin/plink2")
    app.config["GEMMA_WRAPPER_COMMAND"] = gemma_wrapper_command(
        app, f"{GN2_PROFILE}/bin/gemma-wrapper")
    app.config["GUIX_GENENETWORK_FILES"] = get_setting(
        app,
        "GUIX_GENENETWORK_FILES",
        f"{GN2_PROFILE}/share/genenetwork2")
    assert_dir(app.config["JS_GUIX_PATH"])
    ## END: Setup profile dependent settings: Remove these eventually ##

    # Cached values
    app.config["GN_VERSION"] = get_setting(app, 'GN_VERSION')
    app.config["HOME"] = get_setting(app, 'HOME')
    app.config["SERVER_PORT"] = get_setting_int(app, 'SERVER_PORT')
    app.config["WEBSERVER_MODE"] = get_setting(app, 'WEBSERVER_MODE')
    app.config["GN2_BASE_URL"] = get_setting(app, 'GN2_BASE_URL')
    app.config["GN2_BRANCH_URL"] = get_setting(app, 'GN2_BRANCH_URL')
    app.config["GN_SERVER_URL"] = get_setting(app, 'GN_SERVER_URL')
    app.config["GN_PROXY_URL"] = get_setting(app, 'GN_PROXY_URL')
    app.config["GN3_LOCAL_URL"] = get_setting(app, 'GN3_LOCAL_URL')
    app.config["SQL_URI"] = get_setting(app, 'SQL_URI')
    app.config["LOG_LEVEL"] = get_setting(app, 'LOG_LEVEL')
    app.config["LOG_LEVEL_DEBUG"] = get_setting_int(app, 'LOG_LEVEL_DEBUG')
    app.config["LOG_SQL"] = get_setting_bool(app, 'LOG_SQL')
    app.config["LOG_SQL_ALCHEMY"] = get_setting_bool(app, 'LOG_SQL_ALCHEMY')
    app.config["LOG_BENCH"] = get_setting_bool(app, 'LOG_BENCH')
    app.config["LOG_FORMAT"] = "%(message)s"    # not yet in use
    app.config["USE_REDIS"] = get_setting_bool(app, 'USE_REDIS')
    app.config["REDIS_URL"] = get_setting(app, 'REDIS_URL')
    app.config["USE_GN_SERVER"] = get_setting_bool(app, 'USE_GN_SERVER')

    app.config["GENENETWORK_FILES"] = get_setting(app, 'GENENETWORK_FILES')
    app.config["JS_GN_PATH"] = get_setting(app, 'JS_GN_PATH')
    # assert_dir(JS_GN_PATH)

    app.config["GITHUB_CLIENT_ID"] = get_setting(app, 'GITHUB_CLIENT_ID')
    app.config["GITHUB_CLIENT_SECRET"] = get_setting(app, 'GITHUB_CLIENT_SECRET')
    app.config["GITHUB_AUTH_URL"] = get_setting(app, "GITHUB_AUTH_URL")
    if app.config["GITHUB_CLIENT_ID"] != 'UNKNOWN' and app.config["GITHUB_CLIENT_SECRET"]:
        app.config["GITHUB_AUTH_URL"] = (
            "https://github.com/login/oauth/authorize?"
            f"client_id={GITHUB_CLIENT_ID}"
            f"&client_secret={GITHUB_CLIENT_SECRET}")
        app.config["GITHUB_API_URL"] = get_setting(app, 'GITHUB_API_URL')

    app.config["ORCID_CLIENT_ID"] = get_setting(app, 'ORCID_CLIENT_ID')
    app.config["ORCID_CLIENT_SECRET"] = get_setting(app, 'ORCID_CLIENT_SECRET')
    app.config["ORCID_AUTH_URL"] = get_setting(app, "ORCID_AUTH_URL")
    if app.config["ORCID_CLIENT_ID"] != 'UNKNOWN' and app.config["ORCID_CLIENT_SECRET"]:
        app.config["ORCID_AUTH_URL"] = (
            "https://orcid.org/oauth/authorize?response_type=code"
            f"&scope=/authenticate&show_login=true&client_id={ORCID_CLIENT_ID}"
            f"&client_secret={ORCID_CLIENT_SECRET}"
            f"&redirect_uri={GN2_BRANCH_URL}n/login/orcid_oauth2")
        app.config["ORCID_TOKEN_URL"] = get_setting(app, 'ORCID_TOKEN_URL')


    app.config["SMTP_CONNECT"] = get_setting(app, 'SMTP_CONNECT')
    app.config["SMTP_USERNAME"] = get_setting(app, 'SMTP_USERNAME')
    app.config["SMTP_PASSWORD"] = get_setting(app, 'SMTP_PASSWORD')

    app.config["TEMPDIR"] = tempdir(app)  # defaults to UNIX TMPDIR
    assert_dir(app.config["TEMPDIR"])

    # ---- Handle specific JS modules
    app.config["JS_GUIX_PATH"] = get_setting(app, "JS_GUIX_PATH")
    assert_dir(app.config["JS_GUIX_PATH"])
    assert_dir(app.config["JS_GUIX_PATH"] + '/cytoscape-panzoom')

    app.config["CSS_PATH"] = get_setting(app, "JS_GUIX_PATH")  # The CSS is bundled together with the JS
    # assert_dir(JS_PATH)

    app.config["JS_TWITTER_POST_FETCHER_PATH"] = get_setting(
        app,
        "JS_TWITTER_POST_FETCHER_PATH",
        js_path(app, "javascript-twitter-post-fetcher"))
    assert_dir(app.config["JS_TWITTER_POST_FETCHER_PATH"])
    assert_file(app.config["JS_TWITTER_POST_FETCHER_PATH"] + "/js/twitterFetcher_min.js")

    app.config["JS_CYTOSCAPE_PATH"] = get_setting(
        app, "JS_CYTOSCAPE_PATH", js_path(app, "cytoscape"))
    assert_dir(app.config["JS_CYTOSCAPE_PATH"])
    assert_file(app.config["JS_CYTOSCAPE_PATH"] + '/cytoscape.min.js')

    # assert_file(PHEWAS_FILES+"/auwerx/PheWAS_pval_EMMA_norm.RData")

    app.config["OAUTH2_CLIENT_ID"] = get_setting(app, 'OAUTH2_CLIENT_ID')
    app.config["OAUTH2_CLIENT_SECRET"] = get_setting(app, 'OAUTH2_CLIENT_SECRET')
    return app
