import json
import re
from urllib.parse import ParseResult, urlencode, urlparse, urlunparse

from flask import Flask, abort, make_response, redirect, request

REDIRECT_MAP = {}


def load_redirect_map(path="foundation.mozilla.org_wagtail_redirects.json"):
    """
    Load the foundation.mozilla.org redirects into memory.
    Not necessary to offload to some external resource like Redis yet.
    """

    global REDIRECT_MAP
    try:
        with open(path) as f:
            REDIRECT_MAP = json.load(f)
    except FileNotFoundError:
        REDIRECT_MAP = {}


load_redirect_map()


def get_keyvalue_redirect(path, query_string, redirect_map, debug=False):
    """
    Checks the in-memory key/value redirect map and returns a redirect response
    if a match is found. Returns None otherwise.
    """
    full_path = "/" + path

    # Normalize: try as-is and strip trailing slash
    candidates = [full_path]
    if full_path.endswith("/"):
        candidates.append(full_path.rstrip("/"))
    else:
        candidates.append(full_path + "/")

    # Also try full_path + query
    if query_string:
        candidates = [f"{p}?{query_string}" for p in candidates] + candidates

    # Try each candidate
    for candidate in candidates:
        redirect_entry = redirect_map.get(candidate)
        if redirect_entry:
            redirect_url = redirect_entry["redirect_to"]

            # If candidate didn't include query string, but the request did, add it
            if "?" not in candidate and query_string:
                separator = "&" if "?" in redirect_url else "?"
                redirect_url = f"{redirect_url}{separator}{query_string}"

            status_code = 301 if redirect_entry.get("is_permanent") else 302

            if debug:
                print(f"[kv redirect] {candidate} → {redirect_url} ({status_code})")

            return redirect(redirect_url, code=status_code)

    return None


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)

    if test_config is None:
        app.config.from_object("config.Config")
    else:
        app.config.update(test_config)

    redirect_rules = app.config["REDIRECT_RULES"]
    force_ssl = app.config["FORCE_SSL"]
    debug = app.config["DEBUG"]

    @app.before_request
    def enforce_ssl():
        if not force_ssl:
            return None

        proto = request.headers.get("X-Forwarded-Proto", None)

        if proto == "https":
            return None

        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

    @app.route("/robots.txt")
    def send_robots_txt():
        response = make_response("User-agent: *\n")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    def handle_donate_mozilla_org(path):
        """
        Strips language codes from the URL path, redirecting to '/donate/' or its approved subpaths if specified.
        """
        # Regex pattern to identify language codes (EX: /en-US/, /fr/)
        language_code_regex = re.compile(r"^[a-z]{2}(-[A-Z]{2}|-[A-Z][a-z])?/?$")
        # The default donate path
        donate_path = "/donate/"
        # Donate subpaths that exist on foundation.mozilla.org
        donate_subpaths = ["faq", "help", "ways-to-give"]

        if path:
            # Strip language codes from the path and reconstruct it,
            path_segments = path.strip("/").split("/")
            filtered_segments = [segment for segment in path_segments if not language_code_regex.match(segment)]
            cleaned_path = "/".join(filtered_segments)

            if cleaned_path in donate_subpaths:
                donate_path += cleaned_path

        return donate_path

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def redirector(path):
        x_forwarded_host = request.headers.get("X-Forwarded-Host", None)

        if x_forwarded_host:
            host = x_forwarded_host
        else:
            host = request.headers.get("Host", None)

        if debug:
            print("received request from {}".format(host))

        # Special handling for donate.mozilla.org requests
        if "donate.mozilla.org" in host:
            path = handle_donate_mozilla_org(path)

        # Prevent redirect for resources such as JS, CSS and images and return HTTP 410 Gone
        if path.endswith((".js", ".css", ".png", ".svg", ".ico", ".txt")):
            return abort(410)

        # Use key/value redirects to short-circuit foundation.mozilla.org's redirect rule only
        # Note redirect.mozillafoundation.org for testing until domain switch is live.
        if "redirect.mozillafoundation.org" in host:
            keyvalue_response = get_keyvalue_redirect(path, request.query_string.decode("utf-8"), REDIRECT_MAP, debug)
            if keyvalue_response:
                return keyvalue_response

        if host in redirect_rules:
            redirect_target, redirect_code, preserves = redirect_rules[host]
            preserve_path, preserve_query = preserves

            redirect_path = ""
            redirect_query = ""

            target_url = urlparse(redirect_target)

            if preserve_path:
                redirect_path = path
            else:
                redirect_path = target_url.path

            if preserve_query:
                redirect_query = urlencode(request.args, doseq=True)
            else:
                redirect_query = target_url.query

            redirect_parse = ParseResult(
                scheme=target_url.scheme,
                netloc=target_url.netloc,
                path=redirect_path,
                query=redirect_query,
                params="",
                fragment="",
            )

            final_redirect = urlunparse(redirect_parse)

            if debug:
                print("redirecting to {} with a {}".format(final_redirect, redirect_code.value))

            return redirect(final_redirect, code=redirect_code.value)

        return abort(400)

    @app.after_request
    def response_headers(response):
        response.headers["Server"] = "MoFo Redirector"
        return response

    return app


if __name__ == "__main__":
    create_app().run()
