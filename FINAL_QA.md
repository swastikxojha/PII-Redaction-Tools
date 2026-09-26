# Final QA Record

## Execution
- Python compilation: passed (`python -m compileall -q app run.py`)
- Automated tests: 13 passed (`pytest -q`)
- End-to-end redaction: completed against the supplied 127-page Red Herring Prospectus
- Verification: passed with `leak_count = 0`
- Visual QA: rendered output inspected across all 124 rendered pages

## Full-document processing
- Body paragraphs: 1006
- Tables: 76
- Table cells: 3722
- Header paragraphs: 85
- Footer paragraphs: 85
- Embedded images: 8
- Images OCR processed: 8
- Images visually redacted: 2
- Output DOCX structure counts match the source for paragraphs, tables, sections, headers, footers, and images.

## Evaluation benchmark
- 5 benchmark cases
- 25 gold entities
- TP: 25
- FP: 0
- FN: 0
- Entity precision: 1.000
- Entity recall: 1.000
- Entity F1: 1.000
- Character-level accuracy: 1.000

These metrics describe only the small, transparent benchmark included with the take-home solution; they are not claims of universal performance.

## Environment note
The execution environment did not contain `streamlit`, `phonenumbers`, or the `en_core_web_sm` spaCy model. The implementation therefore used documented fallbacks for those components. Tesseract, Pillow, python-docx, spaCy, and Faker were available. The UI code passed compilation but could not be launched in this environment without installing Streamlit.
