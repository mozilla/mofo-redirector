from config import ReturnCodes

from app import REDIRECT_MAP, create_app


def assert_redirect(response, expected_status_code, expected_location):
    assert response.status_code == expected_status_code
    assert response.headers["Location"] == expected_location


def assert_robots(response):
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "User-agent: *\nDisallow: /"


def client(rules):
    config = {"REDIRECT_RULES": rules, "FORCE_SSL": False, "DEBUG": False}
    return create_app(config).test_client()


def test_permanent_redirect():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.PERMANENT, (False, False))})

    r = test_client.get("/", headers=[("Host", "example.com")])

    assert_redirect(r, 301, "https://another-example.com")


def test_temporary_redirect():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.TEMPORARY, (False, False))})

    r = test_client.get("/", headers=[("Host", "example.com")])

    assert_redirect(r, 307, "https://another-example.com")


def test_keep_query():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.TEMPORARY, (False, True))})

    r = test_client.get("/", headers=[("Host", "example.com")], query_string="such_query=very_value")

    assert_redirect(r, 307, "https://another-example.com?such_query=very_value")


def test_keep_path():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.TEMPORARY, (True, False))})

    r = test_client.get("/path/", headers=[("Host", "example.com")])

    assert_redirect(r, 307, "https://another-example.com/path/")


def test_keep_path_and_query():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.TEMPORARY, (True, True))})

    r = test_client.get("/path/", headers=[("Host", "example.com")], query_string="such_query=very_value")

    assert_redirect(r, 307, "https://another-example.com/path/?such_query=very_value")


def test_robots():
    test_client = client({"example.com": ("https://another-example.com", ReturnCodes.TEMPORARY, (True, False))})

    r = test_client.get("/robots.txt", headers=[("Host", "example.com")])

    assert_robots(r)


def test_donate_mozilla_org_redirect_handling():
    """
    Validates redirection logic for donate.mozilla.org, ensuring correct path handling,
    removal of language codes, and preservation of query parameters.
    """
    test_client = client(
        {
            "donate.mozilla.org": (
                "https://foundation.mozilla.org",
                ReturnCodes.PERMANENT,
                (True, True),
            ),
        }
    )

    # Test that an approved path with a language code redirects correctly
    response = test_client.get("/en-US/help", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/help")

    # Test that an unapproved path with a language code defaults to /donate/
    response = test_client.get("/fr/unapproved-path", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/")

    # Test redirection for an approved path without a language code
    response = test_client.get("/ways-to-give", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/ways-to-give")

    # Test redirection for a path that includes multiple language codes
    response = test_client.get("/en-US/es-MX/faq", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/faq")

    # Test redirection for a path that resembles a language code but is not approved
    response = test_client.get("/custom-en-section", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/")

    # Test redirection with query parameters preserved
    response = test_client.get("/en-US/?q=donate", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/?q=donate")

    # Test redirection for the root path
    response = test_client.get("/", headers=[("Host", "donate.mozilla.org")])
    assert_redirect(response, 301, "https://foundation.mozilla.org/donate/")


def test_keyvalue_redirect_exact_match():
    # Inject key/value redirect map for this test
    REDIRECT_MAP.clear()
    REDIRECT_MAP["/about/trademarks"] = {
        "redirect_to": "https://mozillafoundation.org/en/who-we-are/licensing/",
        "is_permanent": True,
    }

    test_client = client({})  # No host rules needed

    response = test_client.get("/about/trademarks", headers=[("Host", "redirect.mozillafoundation.org")])
    assert_redirect(response, 301, "https://mozillafoundation.org/en/who-we-are/licensing/")


def test_keyvalue_redirect_with_query_string():
    REDIRECT_MAP.clear()
    REDIRECT_MAP["/about/trademarks/?q=test&utf=a_campaign"] = {
        "redirect_to": "https://mozillafoundation.org/en/who-we-are/licensing/?q=test&utf=a_campaign",
        "is_permanent": False,
    }

    test_client = client({})

    response = test_client.get(
        "/about/trademarks", query_string="q=test&utf=a_campaign", headers=[("Host", "redirect.mozillafoundation.org")]
    )
    assert_redirect(
        response, 302, "https://mozillafoundation.org/en/who-we-are/licensing/?q=test&utf=a_campaign"
    )
