from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ResourceType(StrEnum):
    EC2 = "EC2"
    EBS = "EBS"
    RDS = "RDS"
    S3 = "S3"
    ELASTIC_IP = "ELASTIC_IP"
    LOAD_BALANCER = "LOAD_BALANCER"
    LAMBDA = "LAMBDA"
    CLOUDFRONT = "CLOUDFRONT"
    NAT_GATEWAY = "NAT_GATEWAY"
    OTHER = "OTHER"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ImpactType(StrEnum):
    OBSERVED_COST = "OBSERVED_COST"
    CALCULATED_ESTIMATE = "CALCULATED_ESTIMATE"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Resource(DomainModel):
    resource_id: str
    resource_type: ResourceType
    account_id: str | None = None
    region: str | None = None
    state: str | None = None
    instance_type: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    creation_date: datetime | None = None
    configuration: dict[str, object] = Field(default_factory=dict)


class CostRecord(DomainModel):
    account_id: str | None = None
    region: str | None = None
    service: str
    resource_id: str | None = None
    date: date
    amount: Decimal
    currency: str = "USD"
    source: str
    is_estimate: bool = False


class UtilizationRecord(DomainModel):
    resource_id: str
    metric: str
    period_start: datetime
    period_end: datetime
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    unit: str | None = None
    source: str


class Finding(DomainModel):
    finding_id: str
    resource_id: str | None = None
    resource_type: ResourceType | None = None
    signal: str
    evidence: list[str] = Field(min_length=1)
    analysis: str
    recommendation: str
    priority: Priority | None = None
    confidence: str | None = None
    potential_impact: Decimal | None = None
    impact_type: ImpactType = ImpactType.UNKNOWN
    owner: str | None = None
    status: FindingStatus = FindingStatus.OPEN
    created_at: datetime
    updated_at: datetime


class GovernanceFinding(DomainModel):
    finding_id: str
    resource_id: str
    required_attribute: str
    current_value: str | None = None
    expected_value: str | None = None
    status: str
    evidence: list[str] = Field(min_length=1)
    owner: str | None = None
