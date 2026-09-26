from __future__ import annotations

from app.models.entity import PIIEntity, PIIType
from app.pseudonymization.generators import SyntheticGenerator


class Pseudonymizer:
    def __init__(self, seed: int = 20250925):
        self.generator=SyntheticGenerator(seed)
        self.mapping: dict[tuple[str,str],str] = {}

    @staticmethod
    def _key(entity: PIIEntity) -> tuple[str,str]:
        normalized=" ".join(entity.value.strip().split()).casefold()
        return entity.type.value, normalized

    def replacement_for(self, entity: PIIEntity) -> str:
        key=self._key(entity)
        if key in self.mapping:
            return self.mapping[key]
        t=entity.type
        g=self.generator
        funcs={
            PIIType.PERSON: lambda k: g.person(k, max_len=len(entity.value.strip())),
            PIIType.RELATIVE_NAME: lambda k: g.person(k, max_len=len(entity.value.strip())),
            PIIType.EMAIL: g.email,
            PIIType.PHONE: g.phone,
            PIIType.COMPANY: lambda k: g.company(k, max_len=len(entity.value.strip())),
            PIIType.ADDRESS: g.address,
            PIIType.DOB: g.dob,
            PIIType.SSN: g.ssn,
            PIIType.CREDIT_CARD: g.credit_card,
            PIIType.IP_ADDRESS: g.ip,
            PIIType.PAN: g.pan,
            PIIType.AADHAAR: g.aadhaar,
            PIIType.PASSPORT: g.passport,
            PIIType.VOTER_ID: g.voter,
            PIIType.BANK_ACCOUNT: g.bank_account,
            PIIType.IFSC: g.ifsc,
            PIIType.GSTIN: g.gstin,
            PIIType.GOVERNMENT_ID: lambda k: "SYNTH-ID-"+str(g._salted_int(k, 1_000_000)).zfill(6),
            PIIType.UPI: lambda k: g.email(k).replace("@example.com", "@example"),
        }
        fn=funcs.get(t, lambda k: "[REDACTED]")
        base_key=f"{t.value}:{key[1]}"
        value=fn(base_key)
        used={v for (typ,_),v in self.mapping.items() if typ==t.value}
        if value in used and t in (PIIType.PERSON, PIIType.RELATIVE_NAME, PIIType.COMPANY):
            for salt in range(1, 1000):
                candidate=fn(base_key+f":{salt}")
                if candidate not in used:
                    value=candidate
                    break
        self.mapping[key]=value
        return value

    def pseudonymize(self, entities: list[PIIEntity]) -> dict[tuple[str,str],str]:
        for e in entities:
            self.replacement_for(e)
        return dict(self.mapping)
