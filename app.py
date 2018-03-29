from flask import (
    Flask,
    request,
    redirect,
    abort,
)

app = Flask(__name__, static_folder=None)

app.config.from_object('config.Config')

redirect_rules = app.config['REDIRECT_RULES']


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirector(path):
    host = request.headers.get('Host', None)

    for request_host, redirect_target, redirect_code in redirect_rules:
        if host == request_host:
            redirect_url = redirect_target
            print(app.config['APPEND_FROM'])
            if app.config['APPEND_FROM']:
                redirect_url += '?from={}'.format(request_host)

            return redirect(redirect_url, code=redirect_code)

    return abort(400)


if __name__ == '__main__':
    app.run()
