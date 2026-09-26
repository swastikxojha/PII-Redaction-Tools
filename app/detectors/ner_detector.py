from __future__ import annotations

from app.detectors.base import BaseDetector, DetectionContext
from app.models.entity import PIIEntity, PIIType, TextContext


class OptionalSpacyNERDetector(BaseDetector):
    """Optional spaCy NER layer. The pipeline remains usable when the model is unavailable."""

    name = "spacy-ner"
    categories = (PIIType.PERSON, PIIType.COMPANY)

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name=model_name
        self._nlp=None
        self.available=False
        try:
            import spacy
            self._nlp=spacy.load(model_name)
            self.available=True
        except Exception:
            self._nlp=None

    def detect(self, text: str, context: DetectionContext):
        if not self._nlp or not text.strip():
            return []
        doc=self._nlp(text)
        out=[]
        for ent in doc.ents:
            typ=PIIType.PERSON if ent.label_=="PERSON" else PIIType.COMPANY if ent.label_=="ORG" else None
            if not typ:
                continue
            conf=0.82
            out.append(PIIEntity(typ,ent.text,ent.start_char,ent.end_char,conf,self.name,TextContext(context.location,context.block_id,context.page)))
        return out
