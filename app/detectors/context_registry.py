from __future__ import annotations

from app.detectors.base import BaseDetector, DetectionContext
from app.detectors.contextual_detector import ContextualDetector
from app.detectors.regex_detector import StructuredRegexDetector
from app.detectors.phone_detector import PhoneDetector
from app.detectors.ner_detector import OptionalSpacyNERDetector
from app.detectors.indian_id_detector import IndianIDDetector


class DetectorPipeline:
    """Composable detection pipeline. New detectors can be registered without modifying orchestration."""

    def __init__(self, detectors: list[BaseDetector] | None = None):
        self.detectors = detectors or [StructuredRegexDetector(), IndianIDDetector(), PhoneDetector(), OptionalSpacyNERDetector(), ContextualDetector()]

    def detect(self, text: str, context: DetectionContext):
        entities=[]
        for detector in self.detectors:
            try:
                entities.extend(detector.detect(text, context))
            except Exception:
                # One detector should never prevent the rest of the document from being processed.
                continue
        return entities
