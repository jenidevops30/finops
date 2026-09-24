import pytest


@pytest.fixture
def base_env(monkeypatch):
    monkeypatch.setenv("FINOPS_ENV", "test")
    monkeypatch.setenv("FINOPS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("FINOPS_AWS_REGION", "eu-west-1")
    monkeypatch.setenv("FINOPS_AWS_READ_ONLY", "true")
    monkeypatch.setenv("FINOPS_REQUIRED_TAGS", "Owner,Environment")
