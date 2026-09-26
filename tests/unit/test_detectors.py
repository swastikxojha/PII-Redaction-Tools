from app.detectors.context_registry import DetectorPipeline
from app.detectors.base import DetectionContext
from app.processors.text_processor import TextProcessor


def detect(text):
    return TextProcessor(DetectorPipeline(), 0.80).detect(text, DetectionContext(location='test', block_id='x'))


def types(text):
    return {(e.type.value,e.value) for e in detect(text)}


def test_structured_required_types():
    found=types('Email john.smith@example.com Phone +91 9876543210 SSN 123-45-6789 IP 192.168.1.10')
    assert ('EMAIL','john.smith@example.com') in found
    assert any(t=='PHONE' for t,v in found)
    assert ('SSN','123-45-6789') in found
    assert ('IP_ADDRESS','192.168.1.10') in found


def test_credit_card_requires_context_and_luhn():
    found=types('Credit Card: 4111 1111 1111 1111')
    assert ('CREDIT_CARD','4111 1111 1111 1111') in found
    assert not any(t=='CREDIT_CARD' for t,v in types('Reference: 4111 1111 1111 1112'))


def test_dob_is_contextual():
    assert any(t=='DOB' for t,v in types('Date of Birth: 01/02/2000'))
    assert not any(t=='DOB' for t,v in types('Report date: 01/02/2000'))


def test_company_and_address():
    found=types('Example Technologies Private Limited, Address: 123 Main Street, Denver, CO 80202')
    assert any(t=='COMPANY' for t,v in found)
    assert any(t=='ADDRESS' for t,v in found)


def test_indian_identifiers():
    found=types('PAN: ABCDE1234F Aadhaar: 1234 5678 9012 IFSC: HDFC0001234 Passport: A1234567')
    assert ('PAN','ABCDE1234F') in found
    assert ('AADHAAR','1234 5678 9012') in found
    assert ('IFSC','HDFC0001234') in found
    assert ('PASSPORT','A1234567') in found


def test_upi_and_bank_account_context():
    found=types('UPI ID: john@example Bank Account: 123456789012')
    assert ('UPI','john@example') in found
    assert any(t=='BANK_ACCOUNT' for t,v in found)
