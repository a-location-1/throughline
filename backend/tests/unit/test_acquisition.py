import pytest

from throughline.acquisition import validate_url


def test_url_requires_public_http_scheme():
    with pytest.raises(ValueError):
        validate_url("file:///tmp/play.txt")
    with pytest.raises(ValueError):
        validate_url("https://user:pass@example.org/play")


def test_localhost_is_rejected():
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1/play")
