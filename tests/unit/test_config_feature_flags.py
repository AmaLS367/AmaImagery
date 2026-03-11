import app.config as cfg


def test_feature_flags_parse_string_booleans_from_json():
    settings = cfg.Settings(FEATURE_FLAGS='{"image_generation":"false","batch_generation":"true","ip_adapter":"0"}')

    assert settings.feature_flags["image_generation"] is False
    assert settings.feature_flags["batch_generation"] is True
    assert settings.feature_flags["ip_adapter"] is False


def test_feature_flags_parse_string_booleans_from_pairs():
    settings = cfg.Settings(FEATURE_FLAGS="image_generation=false;batch_generation=true;ip_adapter=off")

    assert settings.feature_flags["image_generation"] is False
    assert settings.feature_flags["batch_generation"] is True
    assert settings.feature_flags["ip_adapter"] is False
