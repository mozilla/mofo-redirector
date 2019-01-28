# MoFo-Redirector

[![Build Status](https://travis-ci.org/mozilla/mofo-redirector.svg?branch=master)](https://travis-ci.org/mozilla/mofo-redirector)

The MoFo-Redirector is a small Flask application that serves to redirect deprecated and unused MoFo Domains.

The domains served by the redirect are defined as Tuples in config.py:

`('example.com', 'https://foundation.mozilla.org', 301)`

The first value is the Host header value to match in an incoming request. The second is the target of the redirect. The third value is the redirect code to use.

## How to add a new redirect

- Create a PR (instruction in `config.py`),
- Wait for review and merge,
- Detach the domain from current heroku app, attach it to mofo-redirector,
- in Route53 update the Hosted Zone record for redirected domain to point to the redirector heroku app.
