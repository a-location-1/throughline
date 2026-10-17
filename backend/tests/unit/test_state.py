import pytest

from throughline.state import RateLimiter


def test_rate_limiter_enforces_bucket_limit():
    limiter = RateLimiter({"analysis": (1, 60)})
    assert limiter.allow("client", "analysis")
    assert not limiter.allow("client", "analysis")


def test_rate_limiter_is_partitioned_by_client_and_bucket():
    limiter = RateLimiter({"analysis": (1, 60), "logs": (1, 60)})
    assert limiter.allow("client-a", "analysis")
    assert limiter.allow("client-b", "analysis")
    assert limiter.allow("client-a", "logs")


def test_rate_limiter_rejects_unknown_bucket():
    with pytest.raises(KeyError):
        RateLimiter({"analysis": (1, 60)}).allow("client", "logs")
