from __future__ import annotations

import ipaddress
import re


def valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def luhn_valid(value: str) -> bool:
    digits=[int(c) for c in re.sub(r"\D", "", value)]
    if not 13 <= len(digits) <= 19: return False
    total=0
    parity=len(digits)%2
    for i,d in enumerate(digits):
        if i%2==parity:
            d*=2
            if d>9:d-=9
        total+=d
    return total%10==0
