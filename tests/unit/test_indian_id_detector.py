from app.detectors.indian_id_detector import IndianIDDetector
from app.detectors.base import DetectionContext


def test_pan_and_aadhaar_context():
    text = "PAN: ABCDE1234F | Aadhaar: 1234 5678 9012"
    found = IndianIDDetector().detect(text, DetectionContext(location="test", block_id="1"))
    assert {e.type.value for e in found} == {"PAN", "AADHAAR"}
