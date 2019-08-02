from app import create_app
from config import ReturnCodes


def assert_redirect(response, expected_status_code, expected_location):
    assert response.status_code == expected_status_code
    assert response.headers["Location"] == expected_location


def client(rules):
    config = {
        "REDIRECT_RULES": rules,
        "FORCE_SSL": False,
        "DEBUG": False
    }
    return create_app(config).test_client()


def test_permanent_redirect():
    test_client = client(
        {'example.com': (
            "https://another-example.com",
            ReturnCodes.PERMANENT,
            (False, False)
        )}
    )

    r = test_client.get("/", headers=[("Host", "example.com")])

    assert_redirect(r, 301, "https://another-example.com")


def test_temporary_redirect():
    test_client = client(
        {'example.com': (
            "https://another-example.com",
            ReturnCodes.TEMPORARY,
            (False, False)
        )}
    )

    r = test_client.get("/", headers=[("Host", "example.com")])

    assert_redirect(r, 307, "https://another-example.com")


def test_keep_query():
    test_client = client(
        {'example.com': (
            "https://another-example.com",
            ReturnCodes.TEMPORARY,
            (False, True)
        )}
    )

    r = test_client.get("/", headers=[("Host", "example.com")], query_string="such_query=very_value")

    assert_redirect(r, 307, "https://another-example.com?such_query=very_value")


def test_keep_path():
    test_client = client(
        {'example.com': (
            "https://another-example.com",
            ReturnCodes.TEMPORARY,
            (True, False)
        )}
    )

    r = test_client.get("/robots.txt", headers=[("Host", "example.com")])

    assert_redirect(r, 307, "https://another-example.com/robots.txt")


def test_keep_path_and_query():
    test_client = client(
        {'example.com': (
            "https://another-example.com",
            ReturnCodes.TEMPORARY,
            (True, True)
        )}
    )

    r = test_client.get("/robots.txt", headers=[("Host", "example.com")], query_string="such_query=very_value")

    assert_redirect(r, 307, "https://another-example.com/robots.txt?such_query=very_value")
