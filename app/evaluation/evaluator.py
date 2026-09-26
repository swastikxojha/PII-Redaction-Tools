from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from app.detectors.base import DetectionContext
from app.evaluation.metrics import precision, recall, f1
from app.models.entity import PIIType


class Evaluator:
    """Entity-level evaluation against a reviewed JSON benchmark."""

    def __init__(self, detector):
        self.detector=detector

    def evaluate_cases(self, cases: list[dict]) -> dict:
        per=defaultdict(lambda: {"tp":0,"fp":0,"fn":0})
        all_results=[]
        char_tp=char_tn=char_fp=char_fn=0
        self.detector.prime([c["text"] for c in cases])
        for case in cases:
            text=case["text"]
            gold=case.get("entities",[])
            pred=self.detector.detect(text, DetectionContext(location="evaluation", block_id=case.get("id")))
            gold_mask=[False]*len(text)
            pred_mask=[False]*len(text)
            for g in gold:
                for i in range(max(0,int(g["start"])), min(len(text),int(g["end"]))): gold_mask[i]=True
            for e in pred:
                for i in range(max(0,e.start), min(len(text),e.end)): pred_mask[i]=True
            char_tp += sum(g and p for g,p in zip(gold_mask,pred_mask))
            char_tn += sum((not g) and (not p) for g,p in zip(gold_mask,pred_mask))
            char_fp += sum((not g) and p for g,p in zip(gold_mask,pred_mask))
            char_fn += sum(g and (not p) for g,p in zip(gold_mask,pred_mask))
            matched=set()
            for g in gold:
                typ=g["type"]
                gs=int(g["start"]); ge=int(g["end"])
                found=None
                for i,e in enumerate(pred):
                    if i in matched or e.type.value != typ: continue
                    # Exact span match is the primary metric. Exact value match with same class is a fallback.
                    if e.start==gs and e.end==ge:
                        found=i; break
                if found is not None:
                    matched.add(found); per[typ]["tp"] += 1
                else:
                    per[typ]["fn"] += 1
            for i,e in enumerate(pred):
                if i not in matched:
                    per[e.type.value]["fp"] += 1
            all_results.append({"id":case.get("id"),"gold":gold,"predictions":[self._serialize(e) for e in pred]})
        metrics={}
        total_tp=total_fp=total_fn=0
        for typ,v in sorted(per.items()):
            p=precision(v["tp"],v["fp"]); r=recall(v["tp"],v["fn"])
            metrics[typ]={**v,"precision":p,"recall":r,"f1":f1(p,r)}
            total_tp += v["tp"]; total_fp += v["fp"]; total_fn += v["fn"]
        p=precision(total_tp,total_fp); r=recall(total_tp,total_fn)
        acc=(char_tp+char_tn)/(char_tp+char_tn+char_fp+char_fn) if (char_tp+char_tn+char_fp+char_fn) else 0.0
        return {"per_category":metrics,"overall":{"tp":total_tp,"fp":total_fp,"fn":total_fn,"precision":p,"recall":r,"f1":f1(p,r),"character_accuracy":acc,"character_tp":char_tp,"character_tn":char_tn,"character_fp":char_fp,"character_fn":char_fn},"cases":all_results}

    @staticmethod
    def _serialize(e):
        return {"type":e.type.value,"value":e.value,"start":e.start,"end":e.end,"confidence":e.confidence,"source":e.source}

    @staticmethod
    def load(path: str | Path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
