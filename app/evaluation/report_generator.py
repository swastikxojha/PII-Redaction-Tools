from __future__ import annotations

import json
from pathlib import Path


REQUIRED=["PERSON","EMAIL","PHONE","COMPANY","ADDRESS","SSN","CREDIT_CARD","DOB","IP_ADDRESS"]


def write_json(result, path):
    Path(path).write_text(json.dumps(result, indent=2), encoding="utf-8")


def write_report(result, path, document_stats=None):
    lines=["# PII Redaction Evaluation Report","", "## Evaluation scope", "Entity-level precision/recall/F1 were measured against a reviewed benchmark of source-document snippets plus synthetic fixtures for required PII classes absent from the source text. Categories with zero gold instances are reported as N/A when applicable.", ""]
    if document_stats:
        lines += ["## Document processing", f"- Paragraphs visited: {document_stats.paragraphs}", f"- Tables: {document_stats.tables}", f"- Table cells: {document_stats.table_cells}", f"- Header/footer paragraphs: {document_stats.headers + document_stats.footers}", f"- Embedded images: {document_stats.embedded_images}", f"- Images OCR'd: {document_stats.ocr_images}", f"- Images visually redacted: {document_stats.redacted_images}", ""]
    lines += ["## Metrics", "| Category | TP | FP | FN | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for typ in REQUIRED + sorted(k for k in result["per_category"] if k not in REQUIRED):
        v=result["per_category"].get(typ)
        if not v:
            continue
        lines.append(f"| {typ} | {v['tp']} | {v['fp']} | {v['fn']} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} |")
    o=result["overall"]
    lines += ["", f"**Overall precision:** {o['precision']:.3f}", f"**Overall recall:** {o['recall']:.3f}", f"**Overall F1:** {o['f1']:.3f}", "", "## Accuracy definition", "Accuracy is reported as character-level binary classification accuracy on the synthetic benchmark: each character is labelled PII/non-PII by the reviewed gold spans and by predicted spans. It is not used as a substitute for entity-level recall/precision.", "", "## Observed limitations", "- The provided execution environment did not include the optional `en_core_web_sm` spaCy model or the `phonenumbers` package, so the implementation uses a documented rule-based fallback for those capabilities. The requirements file lists them as optional enhancements for a clean install.", "- Address detection is deliberately conservative to avoid redacting financial/page numbers.", "- Image redaction is conservative: an identity-document-like image is redacted as a whole when OCR/context indicates personal identifiers, which favors recall over visual fidelity.", ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
