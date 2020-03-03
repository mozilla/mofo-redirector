from urllib.parse import (
    urlparse,
    urlunparse,
    urlencode,
    ParseResult,
)
from flask import (
    Flask,
    request,
    redirect,
    abort,
    make_response,
)


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)

    if test_config is None:
        app.config.from_object('config.Config')
    else:
        app.config.update(test_config)

    redirect_rules = app.config['REDIRECT_RULES']
    force_ssl = app.config['FORCE_SSL']
    debug = app.config['DEBUG']

    @app.before_request
    def enforce_ssl():
        if not force_ssl:
            return None

        proto = request.headers.get('X-Forwarded-Proto', None)

        if proto == 'https':
            return None

        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def redirector(path):
        x_forwarded_host = request.headers.get('X-Forwarded-Host', None)

        if x_forwarded_host:
            host = x_forwarded_host
        else:
            host = request.headers.get('Host', None)

        if debug:
            print('received request from {}'.format(host))

        if host in redirect_rules:
            redirect_target, redirect_code, preserves = redirect_rules[host]
            preserve_path, preserve_query = preserves

            redirect_path = ''
            redirect_query = ''

            target_url = urlparse(redirect_target)

            if preserve_path:
                redirect_path = path
            else:
                redirect_path = target_url.path

            if preserve_query:
                redirect_query = urlencode(request.args, doseq=True)

            redirect_parse = ParseResult(
                scheme=target_url.scheme,
                netloc=target_url.netloc,
                path=redirect_path,
                query=redirect_query,
                params='',
                fragment=''
            )

            final_redirect = urlunparse(redirect_parse)

            if debug:
                print('redirecting to {} with a {}'.format(final_redirect, redirect_code.value))

            return redirect(final_redirect, code=redirect_code.value)

        return abort(400)

    @app.route('/robots.txt')
    def send_robots_txt():
        response = make_response('User-agent: *\nDisallow: /')
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response

    @app.after_request
    def response_headers(response):
        response.headers['Server'] = 'MoFo Redirector'
        return response

    return app


if __name__ == '__main__':
    create_app().run()
