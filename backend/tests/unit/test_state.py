import pytest

from throughline.state import AnalysisStore


def test_store_enforces_rate_limit():
    store = AnalysisStore(rate_limit=1)
    store.create()
    with pytest.raises(RuntimeError, match="rate limit"):
        store.create()


def test_reset_removes_analysis():
    store = AnalysisStore()
    item = store.create()
    store.reset(item.analysis_id)
    assert store.get(item.analysis_id) is None
