import pytest

from finops_platform.aws import AwsClientFactory


def test_empty_service_name_is_rejected():
    with pytest.raises(ValueError, match="service_name"):
        AwsClientFactory().client(" ")
