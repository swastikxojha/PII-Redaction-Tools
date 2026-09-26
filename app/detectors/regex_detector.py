from __future__ import annotations

import ipaddress
import re
from typing import Iterable

from app.models.entity import PIIEntity, PIIType, TextContext
from app.detectors.base import BaseDetector, DetectionContext


EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?![\w.-])")
SSN_RE = re.compile(r"(?<!\d)(\d{3}-\d{2}-\d{4})(?!\d)")
IP_RE = re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])")
PAN_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{5}\d{4}[A-Z])(?![A-Z0-9])", re.I)
AADHAAR_RE = re.compile(r"(?<!\d)(\d{4}[ -]\d{4}[ -]\d{4})(?!\d)")
GSTIN_RE = re.compile(r"(?<![A-Z0-9])(\d{2}[A-Z]{5}\d{4}[A-Z]\dZ[A-Z0-9])(?![A-Z0-9])", re.I)
IFSC_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{4}0[A-Z0-9]{6})(?![A-Z0-9])", re.I)
PASSPORT_RE = re.compile(r"(?<![A-Z0-9])([A-Z][0-9]{7})(?![A-Z0-9])")
VOTER_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{3}[0-9]{7})(?![A-Z0-9])", re.I)
CARD_RE = re.compile(r"(?<!\d)((?:\d[ -]?){13,19})(?!\d)")
UPI_RE = re.compile(r"(?<![A-Za-z0-9._%+-])([A-Za-z0-9._-]{2,}@[A-Za-z][A-Za-z0-9._-]{1,})(?![A-Za-z0-9._-])")
DATE_RE = re.compile(
    r"(?<!\d)("
    r"(?:0?[1-9]|[12]\d|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}|"
    r"(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(?:[0-2]?\d|3[01]),?\s+(?:19|20)\d{2}"
    r")(?!\d)", re.I)


def _luhn(value: str) -> bool:
    digits = [int(ch) for ch in re.sub(r"\D", "", value)]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class StructuredRegexDetector(BaseDetector):
    name = "structured-regex"

    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        results: list[PIIEntity] = []
        results.extend(self._email(text, context))
        results.extend(self._ssn(text, context))
        results.extend(self._ip(text, context))
        results.extend(self._pan(text, context))
        results.extend(self._aadhaar(text, context))
        results.extend(self._gstin(text, context))
        results.extend(self._ifsc(text, context))
        results.extend(self._passport(text, context))
        results.extend(self._voter(text, context))
        results.extend(self._cards(text, context))
        results.extend(self._upi(text, context))
        return results

    @staticmethod
    def _entity(t: PIIType, m: re.Match[str], conf: float, source: str, c: DetectionContext) -> PIIEntity:
        return PIIEntity(
            type=t,
            value=m.group(1),
            start=m.start(1),
            end=m.end(1),
            confidence=conf,
            source=source,
            context=TextContext(c.location, c.block_id, c.page),
        )

    def _email(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in EMAIL_RE.finditer(text):
            yield self._entity(PIIType.EMAIL, m, 0.995, self.name, c)

    def _ssn(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in SSN_RE.finditer(text):
            raw = m.group(1)
            if raw.startswith(("000", "666")) or raw[4:6] == "00" or raw[7:] == "0000":
                continue
            yield self._entity(PIIType.SSN, m, 0.99, self.name, c)

    def _ip(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in IP_RE.finditer(text):
            try:
                ipaddress.ip_address(m.group(1))
            except ValueError:
                continue
            yield self._entity(PIIType.IP_ADDRESS, m, 0.995, self.name, c)

    def _pan(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in PAN_RE.finditer(text):
            yield self._entity(PIIType.PAN, m, 0.995, self.name, c)

    def _aadhaar(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in AADHAAR_RE.finditer(text):
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) == 12 and len(set(digits)) > 1:
                yield self._entity(PIIType.AADHAAR, m, 0.995, self.name, c)

    def _gstin(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in GSTIN_RE.finditer(text):
            yield self._entity(PIIType.GSTIN, m, 0.95, self.name, c)

    def _ifsc(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in IFSC_RE.finditer(text):
            yield self._entity(PIIType.IFSC, m, 0.94, self.name, c)

    def _passport(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in PASSPORT_RE.finditer(text):
            before = text[max(0, m.start() - 32):m.start()].casefold()
            if any(k in before for k in ("passport", "passport no", "passport number")):
                yield self._entity(PIIType.PASSPORT, m, 0.96, self.name, c)

    def _voter(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in VOTER_RE.finditer(text):
            before = text[max(0, m.start() - 40):m.start()].casefold()
            if any(k in before for k in ("voter", "epic")):
                yield self._entity(PIIType.VOTER_ID, m, 0.96, self.name, c)

    def _upi(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in UPI_RE.finditer(text):
            before=text[max(0,m.start()-30):m.start()].casefold()
            after=text[m.end():m.end()+30].casefold()
            context = any(k in before+after for k in ("upi", "vpa", "payment address"))
            if context and '.' not in m.group(1).split('@')[-1]:
                yield self._entity(PIIType.UPI, m, 0.95, self.name, c)

    def _cards(self, text: str, c: DetectionContext) -> Iterable[PIIEntity]:
        for m in CARD_RE.finditer(text):
            candidate = m.group(1)
            stripped=candidate.strip()
            lead=len(candidate)-len(candidate.lstrip())
            trail=len(candidate)-len(candidate.rstrip())
            digits = re.sub(r"\D", "", stripped)
            if not 13 <= len(digits) <= 19 or not _luhn(stripped):
                continue
            before = text[max(0, m.start() - 32):m.start()].casefold()
            after = text[m.end():m.end() + 20].casefold()
            has_card_context = any(k in (before + after) for k in ("credit", "card", "visa", "mastercard", "amex", "debit"))
            if not has_card_context:
                continue
            yield PIIEntity(PIIType.CREDIT_CARD, stripped, m.start(1)+lead, m.end(1)-trail, 0.995, self.name, TextContext(c.location,c.block_id,c.page))
