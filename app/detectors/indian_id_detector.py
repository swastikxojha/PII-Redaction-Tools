from __future__ import annotations

import re
from app.detectors.base import BaseDetector, DetectionContext
from app.models.entity import PIIEntity, PIIType, TextContext


class IndianIDDetector(BaseDetector):
    """Detect Indian government/financial identifiers using format + context rules."""

    PATTERNS = {
        PIIType.PAN: re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I),
        PIIType.AADHAAR: re.compile(r"\b(?:\d{4}[ -]?){2}\d{4}\b"),
        PIIType.IFSC: re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.I),
        PIIType.GSTIN: re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b", re.I),
        PIIType.PASSPORT: re.compile(r"\b[A-Z][0-9]{7}\b", re.I),
        PIIType.VOTER_ID: re.compile(r"\b[A-Z]{3}[0-9]{7}\b", re.I),
    }
    CONTEXT = {
        PIIType.PAN: ("pan", "permanent account number"),
        PIIType.AADHAAR: ("aadhaar", "aadhar", "uidai", "unique identification"),
        PIIType.IFSC: ("ifsc", "ifsc code"),
        PIIType.GSTIN: ("gstin", "gst number", "goods and services tax"),
        PIIType.PASSPORT: ("passport", "passport no", "passport number"),
        PIIType.VOTER_ID: ("voter", "epic", "elector", "voter id"),
    }

    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        out: list[PIIEntity] = []
        low = text.casefold()
        for typ, rx in self.PATTERNS.items():
            for m in rx.finditer(text):
                value = m.group(0)
                window = low[max(0, m.start()-60):min(len(text), m.end()+60)]
                hints = self.CONTEXT.get(typ, ())
                if typ in (PIIType.AADHAAR, PIIType.PAN, PIIType.IFSC, PIIType.GSTIN, PIIType.PASSPORT, PIIType.VOTER_ID) and not any(h in window for h in hints):
                    continue
                # Exclude the common YYYYMMDD-looking slice from the generic passport-like pattern.
                if typ == PIIType.PASSPORT and value.isdigit():
                    continue
                conf = 0.97 if any(h in window for h in hints) else 0.84
                out.append(PIIEntity(typ, value, m.start(), m.end(), conf, "indian-id-rule", TextContext(context.location, context.block_id, context.page)))
        return out
