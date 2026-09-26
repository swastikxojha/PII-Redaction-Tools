# PII Redaction Tool

A modular, local-first DOCX redaction pipeline built for the supplied Enterprise Data assignment and tested against the supplied **Red Herring Prospectus**.

## What it does

The tool reads a DOCX, detects PII using a hybrid of structured regular expressions, contextual rules, optional spaCy NER, and validation, then replaces detected text with deterministic synthetic alternatives. It also scans embedded images with OCR; identity-document-like images are conservatively replaced with a neutral redaction panel so text, signatures, photographs, and QR codes cannot remain as visual leaks.

The assignment's nine required classes are preserved:

- Full names
- Email addresses
- Phone numbers
- Company names
- Physical/mailing addresses
- Social Security Numbers (SSNs)
- Credit card numbers
- Dates of birth
- IP addresses

Additional classes supported by the implementation include PAN, Aadhaar, passport, voter/EPIC ID, bank-account identifiers, IFSC, UPI, GSTIN, relationship names, and government-ID placeholders.

## Architecture

```text
DOCX
  -> document/table/header/footer extraction
  -> detector pipeline
       - structured regex
       - phone rules / optional phonenumbers validation
       - optional spaCy NER
       - contextual person/company/address/DOB rules
       - Luhn + ipaddress + format validation
  -> span normalization + overlap resolution
  -> deterministic pseudonymization
  -> run-preserving DOCX text replacement
  -> embedded-image OCR and conservative visual redaction
  -> redacted_output.docx
  -> evaluation + verification
```

The implementation is intentionally modular: detectors return a shared `PIIEntity` type, and a detector registry makes additional recognizers easy to add.

## Project layout

```text
pii-redaction-tool/
├── app/
│   ├── detectors/
│   ├── evaluation/
│   ├── models/
│   ├── processors/
│   ├── pseudonymization/
│   ├── ui/
│   └── utils/
├── evaluation/
├── input/
├── output/
├── tests/
├── run.py
├── README.md
├── requirements.txt
└── pyproject.toml
```

## Installation

Use Python 3.11+.

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The image pipeline also needs a local Tesseract executable. On Linux the command should be `tesseract --version`.

For the optional NER layer, install a spaCy English model in your environment, for example `en_core_web_sm`. The code remains functional without the model because contextual rules are the deterministic fallback.

## Run the redactor

```bash
python run.py redact \
  --input "input/Red Herring Prospectus.docx" \
  --output "output/redacted_output.docx"
```

or simply:

```bash
python run.py
```

## Run tests

```bash
python run.py test
```

The final local run for this submission passed the unit/integration suite.

## Run evaluation

```bash
python run.py evaluate
```

The evaluation creates:

- `evaluation/ground_truth.json`
- `evaluation/evaluation_results.json`
- `evaluation/evaluation_report.md`

The benchmark combines manually reviewed source-document snippets and synthetic fixtures for required classes that are not represented in the textual RHP content.

## Verify the generated output

```bash
python run.py verify
```

Verification checks the output DOCX structure, compares source-detected text PII against the output for exact-value leakage, and verifies the known sensitive image media parts changed.

## UI

A refined Streamlit UI is provided at:

```bash
streamlit run app/ui/streamlit_app.py
```

The UI intentionally hides raw entity values by default and offers a developer/debug mode only for trusted local use.

## Pseudonymization

Replacement values are deterministic and consistent within an entity type. The same original normalized value maps to the same synthetic value throughout the document.

Examples:

```text
PERSON        -> synthetic person name
EMAIL         -> synthetic example.com address
PHONE         -> synthetic +91 number
COMPANY       -> synthetic company name
ADDRESS       -> synthetic address
DOB           -> synthetic date
IP            -> RFC 5737 documentation IP
CREDIT_CARD   -> synthetic Luhn-valid test card
SSN           -> synthetic SSN-like value
```

Company/entity names are included because the assignment explicitly requires company-name redaction, even though public corporate names are not always considered personal PII in other settings.

## False-positive controls

The document contains many ordinary dates, monetary values, page numbers, share counts, registration numbers, and postal codes. The implementation therefore does **not** classify every number/date/capitalized phrase as PII.

- credit-card candidates require Luhn validation and card-related context
- IP candidates are validated with Python's `ipaddress`
- phone detection uses structured patterns and contextual cues; the optional `phonenumbers` package is used when installed
- DOB detection requires DOB/birth-date context
- address detection requires address labels or address-like features near postal codes
- organizations rely on legal-entity patterns and context
- person detection relies on strong name contexts, document-wide name cataloging, and optional spaCy NER

## Images

The supplied RHP contains embedded identity-document images. The image processor OCRs all embedded media and, when identity-document/personal-data signals are present, replaces the entire image canvas with a neutral redaction panel. This is deliberately conservative: it prioritizes visual privacy over keeping non-PII artwork from an identity document.

## Evaluation methodology

Metrics are entity-level exact-span metrics against reviewed ground truth:

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2PR / (P + R)
```

The reported accuracy is character-level binary PII/non-PII classification accuracy over the benchmark. Accuracy is not used as a substitute for recall/precision.

Do not interpret benchmark results as a claim of universal model performance. The benchmark is intentionally small and transparent for a 24-hour take-home assignment; the report documents the observed limitations.

## Privacy / logging

The tool runs locally and does not call external APIs. Logs report counts and processing stages rather than raw PII values.

## Observed full-document run

The supplied Red Herring Prospectus was processed end-to-end. The run visited 1,006 paragraphs, 76 tables, 3,722 table cells, 85 sections with 85 headers and 85 footers, and 8 embedded images. All 8 images were OCR-checked and 2 identity-document-like images were visually redacted. The rendered redacted DOCX is 124 pages; the source renders to 127 pages, with page reflow/blank-space changes near the end of the document.

## Known environment limitation from this run

The provided execution environment did not have `phonenumbers`, Streamlit, or an installed `en_core_web_sm` spaCy model. The core redaction and evaluation pipeline was therefore tested with its deterministic fallback implementations. A clean installation using `requirements.txt` enables the optional libraries.
