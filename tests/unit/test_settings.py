from finops_platform.config import Settings


def test_settings_from_environment(base_env):
    settings = Settings.from_environment()
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.aws_region == "eu-west-1"
    assert settings.aws_read_only is True
    assert settings.required_tags == ("Owner", "Environment")
