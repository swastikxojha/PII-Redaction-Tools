from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.entity import PIIEntity, PIIType


@dataclass
class DetectionContext:
    location: str = "body"
    block_id: str | None = None
    page: int | None = None


class BaseDetector(ABC):
    """Interface for every PII detector."""

    name: str = "base"
    categories: tuple[PIIType, ...] = ()

    @abstractmethod
    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        raise NotImplementedError
