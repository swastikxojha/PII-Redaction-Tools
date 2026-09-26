from app.models.entity import PIIEntity, PIIType
from app.pseudonymization.mapper import Pseudonymizer


def test_deterministic_mapping():
    p=Pseudonymizer(123)
    a=PIIEntity(PIIType.PERSON,'Jane Doe',0,8,.9,'test')
    b=PIIEntity(PIIType.PERSON,'Jane Doe',20,28,.9,'test')
    assert p.replacement_for(a)==p.replacement_for(b)
