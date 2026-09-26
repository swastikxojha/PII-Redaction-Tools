from __future__ import annotations

from collections import Counter

from app.detectors.base import DetectionContext
from app.detectors.context_registry import DetectorPipeline
from app.models.entity import PIIEntity


PRIORITY = {
    "EMAIL": 100,
    "CREDIT_CARD": 99,
    "AADHAAR": 98,
    "PAN": 97,
    "SSN": 96,
    "IP_ADDRESS": 95,
    "PHONE": 94,
    "DOB": 93,
    "IFSC": 92,
    "GSTIN": 91,
    "PASSPORT": 90,
    "VOTER_ID": 89,
    "BANK_ACCOUNT": 88,
    "ADDRESS": 80,
    "COMPANY": 70,
    "RELATIVE_NAME": 60,
    "PERSON": 50,
}


class TextProcessor:
    def __init__(self, pipeline: DetectorPipeline | None = None, threshold: float = 0.80):
        self.pipeline = pipeline or DetectorPipeline()
        self.threshold = threshold

    def prime(self, texts):
        for detector in self.pipeline.detectors:
            prime=getattr(detector, "prime", None)
            if prime:
                prime(texts)

    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        raw = self.pipeline.detect(text, context)
        filtered = [e for e in raw if e.confidence >= self.threshold and e.value.strip()]
        return self._resolve_overlaps(self._dedupe(filtered))

    def _resolve_overlaps(self, entities: list[PIIEntity]) -> list[PIIEntity]:
        # Prefer the most specific/high-confidence span; then resolve ties by detector priority.
        ordered = sorted(
            entities,
            key=lambda e: (e.start, -(e.end-e.start), -e.confidence, -PRIORITY.get(e.type.value, 0)),
        )
        kept: list[PIIEntity] = []
        for e in sorted(ordered, key=lambda x: (x.start, x.end)):
            overlaps = [k for k in kept if e.overlaps(k)]
            if not overlaps:
                kept.append(e); continue
            replace = False
            for k in overlaps:
                score_e = (PRIORITY.get(e.type.value, 0), e.confidence, e.end-e.start)
                score_k = (PRIORITY.get(k.type.value, 0), k.confidence, k.end-k.start)
                if score_e > score_k:
                    kept.remove(k); replace=True
            if replace or not any(e.overlaps(k) for k in kept):
                kept.append(e)
        return sorted(kept, key=lambda e: e.start)

    @staticmethod
    def _dedupe(entities: list[PIIEntity]) -> list[PIIEntity]:
        seen=set(); out=[]
        for e in entities:
            key=(e.type.value,e.start,e.end,e.value.casefold())
            if key not in seen:
                seen.add(key); out.append(e)
        return out

    @staticmethod
    def counts(entities: list[PIIEntity]) -> dict[str, int]:
        return dict(Counter(e.type.value for e in entities))
