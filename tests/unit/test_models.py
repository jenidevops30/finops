from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from finops_platform.domain import (
    CostRecord,
    Finding,
    FindingStatus,
    ImpactType,
    Resource,
    ResourceType,
)


def test_resource_model():
    resource = Resource(
        resource_id="i-123",
        resource_type=ResourceType.EC2,
        tags={"Owner": "platform"},
    )
    assert resource.resource_id == "i-123"
    assert resource.resource_type == ResourceType.EC2


def test_cost_record_marks_observed_data():
    record = CostRecord(
        service="AmazonEC2",
        date=date(2026, 9, 24),
        amount=Decimal("12.34"),
        source="cost-explorer",
    )
    assert record.is_estimate is False


def test_finding_requires_evidence():
    with pytest.raises(ValidationError):
        Finding(
            finding_id="FIN-001",
            signal="test",
            evidence=[],
            analysis="analysis",
            recommendation="review",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


def test_finding_defaults_to_open():
    now = datetime.now(timezone.utc)
    finding = Finding(
        finding_id="FIN-001",
        resource_id="i-123",
        resource_type=ResourceType.EC2,
        signal="low utilization",
        evidence=["30-day CPU average is 7.8%"],
        analysis="Potential underutilization signal",
        recommendation="Review instance sizing",
        impact_type=ImpactType.UNKNOWN,
        created_at=now,
        updated_at=now,
    )
    assert finding.status == FindingStatus.OPEN
