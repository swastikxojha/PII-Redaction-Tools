from app.detectors.regex_detector import StructuredRegexDetector
from app.detectors.contextual_detector import ContextualDetector


class FinancialDetector:
    """Facade for financial/government identifiers and their validation rules."""

    def __init__(self):
        self.structured = StructuredRegexDetector()
        self.contextual = ContextualDetector()

    def detect(self, text, context):
        allowed = {"SSN", "CREDIT_CARD", "PAN", "AADHAAR", "GSTIN", "IFSC", "PASSPORT", "VOTER_ID", "BANK_ACCOUNT", "RELATIVE_NAME"}
        out=[e for e in self.structured.detect(text, context) if e.type.value in allowed]
        out.extend([e for e in self.contextual.detect(text, context) if e.type.value in {"BANK_ACCOUNT", "RELATIVE_NAME"}])
        return out
