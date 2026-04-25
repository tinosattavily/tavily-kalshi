def test_presets_do_not_export_cents_variants():
    import app.domains.analysis.presets as presets

    exported = dir(presets)
    assert "StrategyPresetCents" not in exported
    assert "CAUTIOUS_CENTS" not in exported
    assert "BALANCED_CENTS" not in exported
    assert "AGGRESSIVE_CENTS" not in exported
    assert "PRESETS_CENTS" not in exported
    assert "get_preset_cents" not in exported
