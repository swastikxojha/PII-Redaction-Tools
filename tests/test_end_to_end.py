from pathlib import Path
from app.main import redact, validate_output


def test_supplied_rhp_smoke():
    src=Path(__file__).parents[1]/'input'/'Red Herring Prospectus.docx'
    out=Path(__file__).parents[1]/'tmp'/'test_rhp_redacted.docx'
    if not src.exists():
        return
    stats=redact(src,out)
    assert out.exists()
    v=validate_output(out)
    assert v['valid'] is True
    assert stats.paragraphs > 0
