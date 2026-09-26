from __future__ import annotations

import re

try:
    import phonenumbers
except Exception:
    phonenumbers=None

from app.detectors.base import BaseDetector, DetectionContext
from app.models.entity import PIIEntity, PIIType, TextContext

# Supports Indian mobile/landline formats and common international numbers without treating
# arbitrary long numeric strings as phones.
PHONE_PATTERNS = [
    re.compile(r"(?<!\d)\+?\s*91[\s-]*(?:\(?\d{2,5}\)?[\s-]*)?(?:\d[\s-]?){7,10}(?!\d)"),
    re.compile(r"(?<!\d)0\d{2,4}[\s-]\d{6,8}(?!\d)"),
]


class PhoneDetector(BaseDetector):
    name = "phone"
    categories = (PIIType.PHONE,)

    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        results: list[PIIEntity] = []
        seen=set()
        for rx in PHONE_PATTERNS:
            for m in rx.finditer(text):
                raw_full=m.group(0)
                raw=raw_full.strip()
                lead=len(raw_full)-len(raw_full.lstrip())
                trail=len(raw_full)-len(raw_full.rstrip())
                digits=re.sub(r"\D", "", raw)
                before=text[max(0,m.start()-40):m.start()].casefold()
                after=text[m.end():m.end()+40].casefold()
                contextual=any(k in before+after for k in ("telephone", "tel", "phone", "mobile", "fax", "+91"))
                if not (contextual or raw.startswith("+")):
                    continue
                if not 7 <= len(digits) <= 13:
                    continue
                if phonenumbers is not None:
                    try:
                        parsed=phonenumbers.parse(raw, "IN")
                        if not phonenumbers.is_possible_number(parsed):
                            continue
                    except Exception:
                        pass
                key=(m.start(),m.end())
                if key in seen:
                    continue
                seen.add(key)
                results.append(PIIEntity(
                    type=PIIType.PHONE,
                    value=raw,
                    start=m.start()+lead,
                    end=m.end()-trail,
                    confidence=0.96 if contextual else 0.90,
                    source=self.name,
                    context=TextContext(context.location, context.block_id, context.page),
                ))
        return results
