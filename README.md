# MoFo-Redirector

The MoFo-Redirector is a small Flask application that serves to redirect deprecated and unused MoFo Domains.

The domains served by the redirect are defined as Tuples in config.py:

`('example.com', 'https://foundation.mozilla.org', 301)`

The first value is the Host header value to match in an incoming request. The second is the target of the redirect. The third value is the redirect code to use.
