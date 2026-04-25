from app.domains.markets.adapters.registry import get_adapter_for_url, registered_adapters


def test_registry_resolves_kalshi_url():
    adapter = get_adapter_for_url("https://kalshi.com/markets/INXD-25JAN17-B24999")
    assert adapter.venue == "kalshi"


def test_registry_resolves_polymarket_url():
    adapter = get_adapter_for_url("https://polymarket.com/event/fed-decision")
    assert adapter.venue == "polymarket"


def test_registry_rejects_unknown_url():
    try:
        get_adapter_for_url("https://example.com/event/foo")
    except ValueError as exc:
        assert "Kalshi" in str(exc)
        assert "Polymarket" in str(exc)
    else:
        raise AssertionError("expected unsupported URL")


def test_adapter_claims_do_not_overlap():
    urls = [
        "https://kalshi.com/markets/INXD-25JAN17-B24999",
        "https://polymarket.com/event/fed-decision",
    ]
    for url in urls:
        matches = [adapter.venue for adapter in registered_adapters() if adapter.matches(url)]
        assert len(matches) == 1
