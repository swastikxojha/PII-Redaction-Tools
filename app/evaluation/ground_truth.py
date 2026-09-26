from __future__ import annotations

import json
from pathlib import Path


def build_case(case_id: str, text: str, spans: list[tuple[str,str]]):
    entities=[]
    cursor=0
    for typ, value in spans:
        idx=text.index(value, cursor)
        entities.append({"type":typ,"value":value,"start":idx,"end":idx+len(value)})
        cursor=idx+len(value)
    return {"id":case_id,"text":text,"entities":entities}


def write_cases(cases, path):
    Path(path).write_text(json.dumps(cases, indent=2), encoding="utf-8")
