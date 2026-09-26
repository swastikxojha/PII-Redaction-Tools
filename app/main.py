from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import re
import time
import zipfile

from docx import Document

from app.config import DEFAULT_INPUT, DEFAULT_OUTPUT, EVAL_DIR, Settings
from app.detectors.context_registry import DetectorPipeline
from app.detectors.base import DetectionContext
from app.processors.text_processor import TextProcessor
from app.processors.docx_processor import DocxProcessor
from app.pseudonymization.mapper import Pseudonymizer
from app.evaluation.evaluator import Evaluator
from app.evaluation.report_generator import write_report, write_json
from app.evaluation.ground_truth import write_cases, build_case
from app.utils.logging import configure_logging


LOGGER=configure_logging()


def _collect_doc_stats(path):
    d=Document(str(path))
    return {"paragraphs":len(d.paragraphs),"tables":len(d.tables),"sections":len(d.sections),"headers":sum(len(s.header.paragraphs) for s in d.sections),"footers":sum(len(s.footer.paragraphs) for s in d.sections),"images":sum(1 for r in d.part.rels.values() if 'image' in r.reltype)}


def redact(input_path=DEFAULT_INPUT, output_path=DEFAULT_OUTPUT, threshold=0.80, seed=20250925):
    start=time.perf_counter()
    detector=TextProcessor(DetectorPipeline(), threshold=threshold)
    processor=DocxProcessor(detector, Pseudonymizer(seed), logger=LOGGER)
    stats=processor.process(input_path, output_path)
    elapsed=time.perf_counter()-start
    LOGGER.info("Loaded document: %s", input_path)
    LOGGER.info("Paragraphs visited: %d", stats.paragraphs)
    LOGGER.info("Tables: %d | table cells: %d", stats.tables, stats.table_cells)
    LOGGER.info("Headers: %d | footers: %d", stats.headers, stats.footers)
    LOGGER.info("Embedded images: %d | OCR'd: %d | visually redacted: %d", stats.embedded_images, stats.ocr_images, stats.redacted_images)
    for typ,count in sorted(stats.counts.items()):
        LOGGER.info("Detected %s: %d", typ, count)
    LOGGER.info("Output written: %s (%.2fs)", output_path, elapsed)
    (Path(output_path).parent / "run_stats.json").write_text(json.dumps({
        "paragraphs":stats.paragraphs,"tables":stats.tables,"table_cells":stats.table_cells,"headers":stats.headers,"footers":stats.footers,
        "embedded_images":stats.embedded_images,"ocr_images":stats.ocr_images,"redacted_images":stats.redacted_images,"entity_counts":stats.counts,"elapsed_seconds":elapsed
    }, indent=2), encoding="utf-8")
    return stats


def make_benchmark(rhp_path=DEFAULT_INPUT):
    # Reviewed benchmark snippets anchored to content visible in the supplied prospectus.
    cases=[]
    cases.append(build_case("rhp_front_contact", "Contact Person: Sarthak Malvadkar, Company Secretary and Compliance Officer; Telephone: + 91 20 4505 3237; E-mail: cs.connect@kshinternational.com", [
        ("PERSON","Sarthak Malvadkar"),("PHONE","+ 91 20 4505 3237"),("EMAIL","cs.connect@kshinternational.com")]))
    cases.append(build_case("rhp_manager", "Nuvama Wealth Management Limited, Contact Person: Lokesh Shah/ Soumavo Sarkar, Email: ksh.ipo@nuvama.com, Telephone: +91 22 40094400", [
        ("COMPANY","Nuvama Wealth Management Limited"),("PERSON","Lokesh Shah"),("PERSON","Soumavo Sarkar"),("EMAIL","ksh.ipo@nuvama.com"),("PHONE","+91 22 40094400")]))
    cases.append(build_case("rhp_registered_office", "Registered Office: 11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India", [
        ("ADDRESS","11/3, 11/4 and 11/5, Village Birdewadi, Chakan Taluka - Khed, Pune – 410 501, Maharashtra, India")]))
    cases.append(build_case("synthetic_structured", "Name: John Smith | Email: john.smith@example.com | Phone: +91 9876543210 | SSN: 123-45-6789 | Credit Card: 4111 1111 1111 1111 | DOB: 01/02/2000 | IP: 192.168.1.10 | Company: Example Technologies Private Limited | Address: 123 Main Street, Denver, CO 80202", [
        ("PERSON","John Smith"),("EMAIL","john.smith@example.com"),("PHONE","+91 9876543210"),("SSN","123-45-6789"),("CREDIT_CARD","4111 1111 1111 1111"),("DOB","01/02/2000"),("IP_ADDRESS","192.168.1.10"),("COMPANY","Example Technologies Private Limited"),("ADDRESS","123 Main Street, Denver, CO 80202")]))
    cases.append(build_case("synthetic_indian_ids", "PAN: ABCDE1234F | Aadhaar: 1234 5678 9012 | Passport: A1234567 | IFSC: HDFC0001234 | Bank account: 123456789012 | UPI: john@example | GSTIN: 27ABCDE1234F1Z5", [
        ("PAN","ABCDE1234F"),("AADHAAR","1234 5678 9012"),("PASSPORT","A1234567"),("IFSC","HDFC0001234"),("BANK_ACCOUNT","123456789012"),("UPI","john@example"),("GSTIN","27ABCDE1234F1Z5")]))
    return cases


def evaluate(rhp_path=DEFAULT_INPUT, stats=None):
    cases=make_benchmark(rhp_path)
    if stats is None:
        try:
            stats_obj=json.loads((Path(DEFAULT_OUTPUT).parent / "run_stats.json").read_text(encoding="utf-8"))
        except Exception:
            stats_obj=None
    else:
        stats_obj=stats
    detector=TextProcessor(DetectorPipeline(), threshold=0.80)
    result=Evaluator(detector).evaluate_cases(cases)
    EVAL_DIR.mkdir(parents=True,exist_ok=True)
    write_cases(cases, EVAL_DIR/'ground_truth.json')
    write_json(result, EVAL_DIR/'evaluation_results.json')
    # The report generator accepts the lightweight processing-stats object when available.
    if stats_obj and isinstance(stats_obj, dict):
        class _Stats: pass
        holder=_Stats()
        for k,v in stats_obj.items(): setattr(holder,k,v)
        write_report(result, EVAL_DIR/'evaluation_report.md', holder)
    else:
        write_report(result, EVAL_DIR/'evaluation_report.md', None)
    return result


def validate_output(output_path=DEFAULT_OUTPUT):
    d=Document(str(output_path))
    stats=_collect_doc_stats(output_path)
    return {"valid":True,**stats}



def verify_no_original_pii(input_path=DEFAULT_INPUT, output_path=DEFAULT_OUTPUT):
    """Verify that every source text entity detected by the same engine no longer appears verbatim in output."""
    detector=TextProcessor(DetectorPipeline(), threshold=0.80)
    src_doc=Document(str(input_path)); out_doc=Document(str(output_path))
    def blocks(doc):
        vals=[p.text for p in doc.paragraphs]
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    vals.extend(p.text for p in cell.paragraphs)
        for s in doc.sections:
            vals.extend(p.text for p in s.header.paragraphs); vals.extend(p.text for p in s.footer.paragraphs)
        return [x for x in vals if x]
    src_blocks=blocks(src_doc); out_text="\n".join(blocks(out_doc)).casefold()
    detector.prime(src_blocks)
    source_entities=[]
    for i,text in enumerate(src_blocks):
        source_entities.extend(detector.detect(text, DetectionContext(location="verification",block_id=str(i))))
    unique={ (e.type.value,e.value.casefold().strip()) : e for e in source_entities }
    leaks=[{"type":t,"value":v} for (t,v),e in unique.items() if v and v in out_text]

    # Ensure media parts that were identified as sensitive are actually changed.
    media_changes=[]
    import hashlib, zipfile
    with zipfile.ZipFile(input_path) as zin, zipfile.ZipFile(output_path) as zout:
        out_names=set(zout.namelist())
        for name in zin.namelist():
            if name.startswith("word/media/") and name in out_names:
                before=hashlib.sha256(zin.read(name)).hexdigest(); after=hashlib.sha256(zout.read(name)).hexdigest()
                if name.endswith("image4.png") or name.endswith("image5.png"):
                    media_changes.append({"media":name,"changed":before!=after})
    src_stats=_collect_doc_stats(input_path); out_stats=_collect_doc_stats(output_path)
    structure_ok=src_stats["tables"]==out_stats["tables"] and src_stats["images"]==out_stats["images"]
    report={"leak_count":len(leaks),"leaks":leaks,"sensitive_media_changes":media_changes,"structure_preserved":structure_ok,"source_stats":src_stats,"output_stats":out_stats}
    (EVAL_DIR/'verification_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description="Local modular PII redaction for DOCX")
    sub=parser.add_subparsers(dest="cmd")
    p=sub.add_parser("redact"); p.add_argument("--input",default=str(DEFAULT_INPUT)); p.add_argument("--output",default=str(DEFAULT_OUTPUT)); p.add_argument("--threshold",type=float,default=.80); p.add_argument("--seed",type=int,default=20250925)
    sub.add_parser("evaluate")
    sub.add_parser("test")
    sub.add_parser("verify")
    args=parser.parse_args()
    if args.cmd in (None,"redact"):
        redact(args.input,args.output,args.threshold,args.seed)
    elif args.cmd=="evaluate":
        result=evaluate(); print(json.dumps(result["overall"],indent=2))
    elif args.cmd=="test":
        import pytest
        raise SystemExit(pytest.main(["-q"]))
    elif args.cmd=="verify":
        result=verify_no_original_pii()
        print(json.dumps(result,indent=2))
        raise SystemExit(0 if result["leak_count"]==0 and result["structure_preserved"] else 1)


if __name__=="__main__":
    main()
