from __future__ import annotations

import hashlib
import re
from datetime import date, timedelta

try:
    from faker import Faker
except Exception:  # pragma: no cover
    Faker = None


class SyntheticGenerator:
    """Deterministic, local synthetic-value generator."""

    def __init__(self, seed: int = 20250925):
        self.seed = seed
        self.fake = Faker("en_IN") if Faker else None
        if self.fake:
            self.fake.seed_instance(seed)

    def _salted_int(self, key: str, modulo: int = 10_000_000) -> int:
        digest = hashlib.sha256(f"{self.seed}:{key}".encode()).hexdigest()
        return int(digest[:12], 16) % modulo

    def _name_pair(self, key: str, max_len: int | None = None) -> str:
        firsts=[
            "Amy", "Ben", "Ian", "Eva", "Leo", "Max", "Mia", "Raj", "Sam", "Zoe",
            "Ava", "Ana", "Eli", "Kai", "Lia", "Noa", "Nia", "Ria", "Sid", "Tom",
            "Ali", "Dev", "Dia", "Jay", "Jen", "Jim", "Joe", "Joy", "Kim", "Lou",
            "May", "Ned", "Ray", "Roy", "Ruth", "Ryan", "Sean", "Tia", "Uma",
        ]
        lasts=[
            "Doe", "Roe", "Lee", "Roy", "Kim", "Das", "Sen", "Rao", "Shah", "Iye",
            "Nair", "Jain", "Dey", "Paul", "Bose", "Khan", "Seth", "Gill", "Suri", "Pat",
        ]
        combos=[f"{f} {l}" for f in firsts for l in lasts]
        if max_len is not None:
            fitting=[x for x in combos if len(x) <= max_len]
            if fitting:
                combos=fitting
        return combos[self._salted_int(key, len(combos))]

    def person(self, key: str, max_len: int | None = None) -> str:
        return self._name_pair(key, max_len=max_len)

    def company(self, key: str, max_len: int | None = None) -> str:
        prefixes=["Northstar", "Bluepeak", "Evergreen", "Silverline", "Pioneer", "Summit", "Vertex", "Cedar", "Atlas", "Meridian", "Oakridge", "Riverview"]
        industries=["Systems", "Industries", "Logistics", "Advisory", "Networks", "Engineering", "Holdings", "Services", "Manufacturing", "Infrastructure"]
        suffixes=["Ltd", "Private Limited", "LLP"]
        combos=[f"{a} {b} {c}" for a in prefixes for b in industries for c in suffixes]
        if max_len is not None:
            fitting=[x for x in combos if len(x) <= max_len]
            if fitting:
                combos=fitting
        return combos[self._salted_int(key, len(combos))]

    def phone(self, key: str) -> str:
        n=6_000_000_000 + self._salted_int(key, 3_999_999_999)
        raw=str(n)
        return "+91 " + raw[:5] + " " + raw[5:]

    def email(self, key: str) -> str:
        person=self.person(key, max_len=24)
        first,last=[re.sub(r"[^a-z]", "", x.lower()) for x in person.split()]
        suffix=f"{self._salted_int(key, 97):02d}"
        return f"{first}.{last}{suffix}@example.com"

    def address(self, key: str) -> str:
        cities=["Pune", "Mumbai", "Bengaluru", "Delhi", "Hyderabad"]
        city=cities[self._salted_int(key, len(cities))]
        pin=110000 + self._salted_int(key+"pin", 88999)
        return f"42 Example Avenue, Green Park, {city} - {pin}, India"

    def dob(self, key: str) -> str:
        base=date(1970,1,1)
        d=base+timedelta(days=self._salted_int(key, 10_000))
        return d.strftime("%d/%m/%Y")

    def ssn(self, key: str) -> str:
        n=100_000_000 + self._salted_int(key, 899_999_999)
        s=str(n).zfill(9)
        return f"{s[:3]}-{s[3:5]}-{s[5:]}"

    def credit_card(self, key: str) -> str:
        # Visa test-number shape; final digit is computed to satisfy Luhn.
        base="4" + str(self._salted_int(key, 10**14)).zfill(14)
        digits=[int(c) for c in base[:15]]
        checksum=0
        for i,d in enumerate(reversed(digits)):
            if i % 2 == 0:
                d*=2
                if d>9: d-=9
            checksum += d
        check=(10-checksum%10)%10
        num=base[:15]+str(check)
        return " ".join(num[i:i+4] for i in range(0,16,4))

    def ip(self, key: str) -> str:
        return f"192.0.2.{1+self._salted_int(key, 253)}"

    def pan(self, key: str) -> str:
        letters="ABCDEFGHJKLMNPQRSTUVWXYZ"
        idx=self._salted_int(key, 5**5)
        chars=[]
        for _ in range(5):
            chars.append(letters[idx % len(letters)]); idx//=len(letters)
        num=f"{self._salted_int(key+'n', 10_000):04d}"
        return "".join(chars)+num+letters[self._salted_int(key+'l',len(letters))]

    def aadhaar(self, key: str) -> str:
        # Synthetic structure; deliberately not tied to any real identifier.
        a=f"{10_000_000_000 + self._salted_int(key, 89_999_999_999):012d}"
        return f"{a[:4]} {a[4:8]} {a[8:]}"

    def ifsc(self, key: str) -> str:
        return f"EXMP0{self._salted_int(key, 1_000_000):06d}"[:11]

    def passport(self, key: str) -> str:
        letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return letters[self._salted_int(key,26)] + f"{self._salted_int(key+'p',10_000_000):07d}"

    def voter(self, key: str) -> str:
        letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "ABC" + f"{self._salted_int(key,10_000_000):07d}"

    def bank_account(self, key: str) -> str:
        return str(10_000_000_000 + self._salted_int(key,89_999_999_999))

    def gstin(self, key: str) -> str:
        # Example-like value, valid shape rather than tax-record semantics.
        pan=self.pan(key+"pan")
        return "27"+pan+"1Z5"

    def relative_name(self, key: str) -> str:
        return self.person(key+"relative")
