from google_cloud.service import ServiceFactory, DEFAULT_SCOPES


def test_default_scopes_when_no_scopes_passed():
    factory = ServiceFactory(token_file="", secrets_file="")
    assert factory.scopes == DEFAULT_SCOPES


def test_default_scopes_when_none_passed():
    factory = ServiceFactory(token_file="", secrets_file="", scopes=None)
    assert factory.scopes == DEFAULT_SCOPES


def test_passed_in_scopes():
    scopes = ["first-scope", "second-scope"]
    factory = ServiceFactory(token_file="", secrets_file="", scopes=scopes)
    assert factory.scopes == scopes
