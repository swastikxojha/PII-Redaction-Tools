from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PIIType(str, Enum):
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    COMPANY = "COMPANY"
    ADDRESS = "ADDRESS"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    DOB = "DOB"
    IP_ADDRESS = "IP_ADDRESS"
    PAN = "PAN"
    AADHAAR = "AADHAAR"
    PASSPORT = "PASSPORT"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    VOTER_ID = "VOTER_ID"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    IFSC = "IFSC"
    UPI = "UPI"
    GSTIN = "GSTIN"
    GOVERNMENT_ID = "GOVERNMENT_ID"
    RELATIVE_NAME = "RELATIVE_NAME"
    IMAGE = "IMAGE"


@dataclass(frozen=True)
class TextContext:
    location: str = "body"
    block_id: str | None = None
    page: int | None = None


@dataclass
class PIIEntity:
    """Normalized detector result represented as a half-open text span."""

    type: PIIType
    value: str
    start: int
    end: int
    confidence: float
    source: str
    context: TextContext = field(default_factory=TextContext)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def span(self) -> tuple[int, int]:
        return self.start, self.end

    @property
    def normalized_value(self) -> str:
        return " ".join(self.value.strip().split()).casefold()

    def overlaps(self, other: "PIIEntity") -> bool:
        return self.start < other.end and other.start < self.end


REQUIRED_PII_TYPES = {
    PIIType.PERSON,
    PIIType.EMAIL,
    PIIType.PHONE,
    PIIType.COMPANY,
    PIIType.ADDRESS,
    PIIType.SSN,
    PIIType.CREDIT_CARD,
    PIIType.DOB,
    PIIType.IP_ADDRESS,
}
