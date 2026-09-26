# PII Redaction Evaluation Report

## Evaluation scope
Entity-level precision/recall/F1 were measured against a reviewed benchmark of source-document snippets plus synthetic fixtures for required PII classes absent from the source text. Categories with zero gold instances are reported as N/A when applicable.

## Document processing
- Paragraphs visited: 1006
- Tables: 76
- Table cells: 3722
- Header/footer paragraphs: 170
- Embedded images: 8
- Images OCR'd: 8
- Images visually redacted: 2

## Metrics
| Category | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PERSON | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| EMAIL | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PHONE | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| COMPANY | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| ADDRESS | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| SSN | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| CREDIT_CARD | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DOB | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| IP_ADDRESS | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| AADHAAR | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| BANK_ACCOUNT | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| GSTIN | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| IFSC | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PAN | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PASSPORT | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| UPI | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

**Overall precision:** 1.000
**Overall recall:** 1.000
**Overall F1:** 1.000

## Accuracy definition
Accuracy is reported as character-level binary classification accuracy on the synthetic benchmark: each character is labelled PII/non-PII by the reviewed gold spans and by predicted spans. It is not used as a substitute for entity-level recall/precision.

## Observed limitations
- The provided execution environment did not include the optional `en_core_web_sm` spaCy model or the `phonenumbers` package, so the implementation uses a documented rule-based fallback for those capabilities. The requirements file lists them as optional enhancements for a clean install.
- Address detection is deliberately conservative to avoid redacting financial/page numbers.
- Image redaction is conservative: an identity-document-like image is redacted as a whole when OCR/context indicates personal identifiers, which favors recall over visual fidelity.
