from app.domains.markets.canonicalization import canonicalize_url, detect_venue


def test_polymarket_canonical_url_strips_tracking_params():
    assert canonicalize_url(
        "https://polymarket.com/event/foo?utm_source=x&fbclid=y"
    ) == canonicalize_url("https://polymarket.com/event/foo")


def test_canonical_url_lowercases_scheme_and_host_but_keeps_path_case():
    assert canonicalize_url("HTTPS://Polymarket.com/event/Foo?utm_campaign=x") == (
        "https://polymarket.com/event/Foo"
    )


def test_detect_venue_for_supported_hosts():
    assert detect_venue("https://kalshi.com/markets/INXD-25JAN17-B24999") == "kalshi"
    assert detect_venue("https://kalshi.co/events/INXD-25JAN17") == "kalshi"
    assert detect_venue("https://polymarket.com/event/fed-decision") == "polymarket"


def test_detect_venue_rejects_unknown_host():
    try:
        detect_venue("https://example.com/event/foo")
    except ValueError as exc:
        assert "Kalshi" in str(exc)
        assert "Polymarket" in str(exc)
    else:
        raise AssertionError("expected unsupported host error")


def test_detect_venue_rejects_host_with_supported_name_as_substring():
    try:
        detect_venue("https://kalshi.com.attacker.example.com/markets/AAA-1")
    except ValueError:
        pass
    else:
        raise AssertionError("expected unsupported host error")
