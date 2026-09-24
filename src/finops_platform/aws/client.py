"""AWS client boundary for read-only FinOps collectors."""

from dataclasses import dataclass

import boto3
from botocore.client import BaseClient


@dataclass(frozen=True)
class ReadOnlyAwsClient:
    """Named AWS client exposed to collector code."""

    service_name: str
    client: BaseClient


class AwsClientFactory:
    """Create AWS SDK clients through the standard credential provider chain.

    This layer intentionally exposes no infrastructure mutation methods.
    """

    def __init__(self, region_name: str = "us-east-1") -> None:
        self.region_name = region_name

    def client(self, service_name: str) -> ReadOnlyAwsClient:
        if not service_name or not service_name.strip():
            raise ValueError("service_name must not be empty")
        return ReadOnlyAwsClient(
            service_name=service_name,
            client=boto3.client(service_name, region_name=self.region_name),
        )
