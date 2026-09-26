from __future__ import annotations

import re

from app.detectors.base import BaseDetector, DetectionContext
from app.models.entity import PIIEntity, PIIType, TextContext
from app.detectors.regex_detector import DATE_RE

ROLE_WORDS = {
    "company", "secretary", "compliance", "officer", "director", "executive", "chairman", "chief",
    "financial", "manager", "managing", "whole-time", "promoter", "registrar", "contact", "person",
    "banker", "auditor", "analyst", "partner", "counsel", "advocate", "trustee", "engineer", "research",
    "head", "president", "vice", "general", "office", "limited", "private", "ltd", "llp", "trust",
    "family", "india", "indian", "board", "committee", "corporate", "securities", "wealth", "management",
}
STOP_NAME_WORDS = ROLE_WORDS | {"the", "and", "for", "with", "from", "our", "this", "that", "page", "offer", "equity"}

# High-precision names from labels/context. A second pass adds repeats found here.
NAME_LABEL_PATTERNS = [
    re.compile(r"\b(?:Full\s+)?Name\s*:\s*([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,4})"),
    re.compile(r"\bContact\s+Person\s*:\s*([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,4})", re.I),
    re.compile(r"\b(?:being|namely)\s+([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,4})(?=\s*[\.,;])"),
    re.compile(r"\bNAME\s+OF\s+THE\s+(?:PROMOTER\s+SELLING\s+SHAREHOLDER|SHAREHOLDER)\b\s*[:\-]?\s*([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,4})", re.I),
]
PROMOTER_LIST_RE = re.compile(r"\b(?:OUR\s+)?PROMOTERS\s*:\s*(.{0,1200})", re.I | re.S)

ORG_RE = re.compile(
    r"\b(((?!(?i:and|of|the|for)\b)[A-Z0-9][A-Za-z0-9&.\-]*)(?:\s+(?:[A-Z0-9][A-Za-z0-9&.\-]*|(?i:and|of|the|for))){1,8}?\s+(?i:Private\s+Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Inc\.?|Corporation|Corp\.?|Trust|Foundation|Bank|Insurance))\b"
)

ADDRESS_HINTS = (
    "registered office", "corporate office", "office:", "address:", "plot no", "floor", "marg", "road", "street",
    "village", "taluka", "taluk", "district", "near", "area", "building", "park", "complex", "chowk",
)
INDIAN_STATES = (
    "maharashtra", "delhi", "karnataka", "uttar pradesh", "uttarakhand", "gujarat", "tamil nadu", "telangana",
    "west bengal", "rajasthan", "madhya pradesh", "kerala", "punjab", "haryana", "odisha", "bihar", "goa",
)


class ContextualDetector(BaseDetector):
    name = "contextual"

    def detect(self, text: str, context: DetectionContext) -> list[PIIEntity]:
        out: list[PIIEntity] = []
        out.extend(self._companies(text, context))
        out.extend(self._dob(text, context))
        out.extend(self._addresses(text, context))
        out.extend(self._names(text, context))
        out.extend(self._relative_names(text, context))
        out.extend(self._bank_accounts(text, context))
        return out

    def _companies(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out = []
        for m in ORG_RE.finditer(text):
            value = m.group(1).strip(" ,.;:")
            start=m.start(1); end=m.end(1)
            # Strip document labels that precede the actual organization name.
            prefix=re.match(r"(?:(?:registered|corporate)\s+office\s+of\s+)?(?:our\s+)?company\s+", value, re.I)
            if prefix:
                start += prefix.end(); value=value[prefix.end():]
            else:
                label=re.match(r"(?:registered|corporate)\s+office\s+of\s+our\s+", value, re.I)
                if label:
                    start += label.end(); value=value[label.end():]
            if len(value.split()) < 2:
                continue
            out.append(self._e(PIIType.COMPANY, start, end, value, 0.95, c, "organization-rule"))
        return out

    def _dob(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out = []
        for m in DATE_RE.finditer(text):
            before = text[max(0, m.start() - 50):m.start()].casefold()
            after = text[m.end():m.end() + 40].casefold()
            if re.search(r"\b(?:date\s+of\s+birth|dob|d\.o\.b\.?|birth\s+date)\b", before + after):
                out.append(self._e(PIIType.DOB, m.start(1), m.end(1), m.group(1), 0.99, c, "dob-context"))
        return out

    def _addresses(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out = []
        # Addresses in this document are commonly represented as multi-clause spans ending in a 6-digit PIN.
        pin_re = re.compile(r"\b(?:[1-9]\d{5}|[1-9]\d{2}[ -]\d{3}|\d{5}(?:-\d{4})?)\b")
        us_states = re.compile(r"\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b", re.I)
        for pin in pin_re.finditer(text):
            window_start = max(0, text.rfind("\n", 0, pin.start()) + 1)
            window_start = max(0, window_start - 280)
            candidate = text[window_start:pin.end()]
            low = candidate.casefold()
            if not any(h in low for h in ADDRESS_HINTS):
                continue
            label_context = any(k in low for k in ("address:", "registered office", "corporate office", "mailing address", "residence:"))
            strong_hint = any(k in low for k in ("plot no", "floor", "marg", "road", "street", "village", "taluka", "district", "near", "area", "building", "park", "complex", "chowk"))
            if not (label_context or strong_hint or "india" in low or any(s in low for s in INDIAN_STATES) or us_states.search(candidate)):
                continue
            # Prefer an explicit address label; otherwise use the latest strong address cue.
            explicit_labels=("registered office", "corporate office", "mailing address", "address:", "residence:")
            explicit=[candidate.casefold().rfind(h) for h in explicit_labels if candidate.casefold().rfind(h) >= 0]
            if explicit:
                label_start=max(explicit)
                label_text=max((h for h in explicit_labels if candidate.casefold().rfind(h) == label_start), key=len)
                start_rel=label_start+len(label_text)
            else:
                starts=[candidate.casefold().find(h) for h in ADDRESS_HINTS if candidate.casefold().find(h) >= 0]
                # Prefer the beginning of the current line when it looks like an address block.
                same_line_start=text.rfind("\n", 0, pin.start()) + 1
                line_rel=max(0, same_line_start-window_start)
                line_piece=candidate[line_rel:]
                line_strong=any(k in line_piece.casefold() for k in ("plot no", "floor", "marg", "road", "street", "village", "taluka", "district", "near", "area", "building", "park", "complex", "chowk"))
                if line_piece.strip() and line_strong and len(line_piece) <= 240:
                    start_rel=line_rel
                else:
                    start_rel=min(starts) if starts else 0
            raw_addr=candidate[start_rel:]
            addr = raw_addr.lstrip(" \n\t:;,.()-")
            abs_start = window_start + start_rel + (len(raw_addr)-len(addr))
            if len(addr) < 12 or not re.search(r"\d", addr):
                continue
            end=pin.end()
            # Include a short country/state suffix following the postal code (e.g. ", Maharashtra, India").
            tail_match=re.match(r"(?:\s*,\s*[A-Za-z][A-Za-z .-]*){1,3}", text[end:end+60])
            if tail_match and len(tail_match.group(0)) <= 45:
                end += tail_match.end()
            out.append(self._e(PIIType.ADDRESS, abs_start, end, text[abs_start:end], 0.88, c, "address-context"))
        # Context-led addresses with no recognizable PIN are kept out deliberately to preserve precision.
        return self._dedupe(out)

    def prime(self, texts):
        """Collect high-confidence names across the whole document before any mutation."""
        catalog=set(getattr(self, "known_names", set()))
        for text in texts:
            catalog.update(self._strong_names(text))
        self.known_names=catalog

    def _strong_names(self, text: str) -> set[str]:
        found=set()
        for rx in NAME_LABEL_PATTERNS:
            for m in rx.finditer(text):
                raw=m.group(1).strip(" ,.;:")
                # Contact fields frequently contain two people separated by a slash; capture both.
                for v in re.split(r"\s*/\s*", raw):
                    v=v.strip(" ,.;:")
                    if self._looks_like_person(v) and not self._looks_like_company(v):
                        found.add(v)
        contact_list_rx=re.compile(r"\bContact\s+person\s*:\s*([^,;\n]+(?:\s*/\s*[^,;\n]+)?)", re.I)
        for m in contact_list_rx.finditer(text):
            for v in re.split(r"\s*/\s*", m.group(1)):
                v=v.strip(" ,.;:")
                if self._looks_like_person(v) and not self._looks_like_company(v):
                    found.add(v)
        # Promoter/shareholder lists are comma-separated and often all-caps in the prospectus.
        for m in PROMOTER_LIST_RE.finditer(text):
            body=m.group(1)
            for chunk in re.split(r"[,;]|\(\w+\)", body):
                v=chunk.strip(" .:()\t\n")
                if self._looks_like_person(v) and not self._looks_like_company(v):
                    found.add(v)
        # Names immediately preceding common executive-role abbreviations/titles.
        role_rx=re.compile(r"\b([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,3})\s*,\s*(?:CEO|CFO|CS|COO|CTO|Technical Director|Compliance Officer|Company Secretary)\b", re.I)
        for m in role_rx.finditer(text):
            v=re.sub(r"^and\s+", "", m.group(1).strip(), flags=re.I)
            if self._looks_like_person(v) and not self._looks_like_company(v): found.add(v)
        rel_rx=re.compile(r"\b(?:from|to|for)\s+([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,3})\s*,\s*(?:to include|dated|bearing)\b", re.I)
        for m in rel_rx.finditer(text):
            v=re.sub(r"^and\s+", "", m.group(1).strip(), flags=re.I)
            if self._looks_like_person(v) and not self._looks_like_company(v): found.add(v)
        return found

    def _names(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out: list[PIIEntity] = []
        # Strong local patterns.
        for v in self._strong_names(text):
            for m in re.finditer(rf"(?<![A-Za-z]){re.escape(v)}(?![A-Za-z])", text, re.I):
                out.append(self._e(PIIType.PERSON, m.start(), m.end(), m.group(0), 0.96, c, "name-context"))
        # Whole-document catalog catches repeated names after a strong occurrence was found elsewhere.
        for v in sorted(getattr(self, "known_names", set()), key=len, reverse=True):
            for m in re.finditer(rf"(?<![A-Za-z]){re.escape(v)}(?![A-Za-z])", text, re.I):
                out.append(self._e(PIIType.PERSON, m.start(), m.end(), m.group(0), 0.98, c, "known-name-repeat"))
        # In tables, isolated 2-4 token title-case cells are often names. Keep this conservative.
        if c.location == "table" and not self._looks_like_company(text.strip()):
            v=text.strip().strip("/,")
            if self._looks_like_person(v) and len(v.split()) <= 4:
                for m in re.finditer(rf"(?<![A-Za-z]){re.escape(v)}(?![A-Za-z])", text):
                    out.append(self._e(PIIType.PERSON, m.start(), m.end(), m.group(0), 0.86, c, "table-name-shape"))
        return self._dedupe(out)

    def _relative_names(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out = []
        # Only capture names adjacent to an explicit relationship label.
        rx = re.compile(r"\b(?:father(?:'s)?\s+name|mother(?:'s)?\s+name|spouse|husband|wife|guardian)\s*[:\-]\s*([A-Z][A-Za-z'\.-]+(?:\s+[A-Z][A-Za-z'\.-]+){1,3})", re.I)
        for m in rx.finditer(text):
            v = m.group(1).strip()
            if self._looks_like_person(v):
                out.append(self._e(PIIType.RELATIVE_NAME, m.start(1), m.end(1), v, 0.93, c, "relationship-context"))
        return out

    def _bank_accounts(self, text: str, c: DetectionContext) -> list[PIIEntity]:
        out = []
        rx = re.compile(r"\b(?:account(?:\s+(?:no|number|#))?|a/c)\s*[:#-]?\s*([0-9][0-9 -]{7,20})", re.I)
        for m in rx.finditer(text):
            raw_full=m.group(1)
            raw=raw_full.strip()
            digits=re.sub(r"\D", "", raw)
            if 8 <= len(digits) <= 20:
                left=len(raw_full)-len(raw_full.lstrip())
                right=len(raw_full)-len(raw_full.rstrip())
                out.append(self._e(PIIType.BANK_ACCOUNT, m.start(1)+left, m.end(1)-right, raw, 0.90, c, "account-context"))
        return out

    @staticmethod
    def _looks_like_person(value: str) -> bool:
        parts = value.split()
        if not 2 <= len(parts) <= 5:
            return False
        if any(p.casefold() in STOP_NAME_WORDS for p in parts):
            return False
        if any(any(ch.isdigit() for ch in p) for p in parts):
            return False
        def valid_token(p):
            return bool(re.match(r"^(?:[A-Z][A-Za-z'\.-]+|[A-Z]{2,}[A-Z'\.-]*)$", p))
        return all(valid_token(p) for p in parts)

    @staticmethod
    def _looks_like_company(value: str) -> bool:
        low=value.casefold()
        return any(s in low.split() for s in ("limited", "ltd", "llp", "trust", "bank", "corporation", "corp")) or "private limited" in low

    @staticmethod
    def _e(t, s, e, v, conf, c, source):
        return PIIEntity(t, v, s, e, conf, source, TextContext(c.location, c.block_id, c.page))

    @staticmethod
    def _dedupe(entities):
        seen=set(); out=[]
        for e in entities:
            k=(e.type,e.start,e.end,e.value.casefold())
            if k not in seen:
                seen.add(k); out.append(e)
        return out
