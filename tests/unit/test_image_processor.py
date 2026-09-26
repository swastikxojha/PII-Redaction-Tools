from PIL import Image
import io
from app.detectors.context_registry import DetectorPipeline
from app.processors.text_processor import TextProcessor
from app.processors.image_processor import ImageProcessor


def test_non_sensitive_image_survives():
    im=Image.new('RGB',(100,100),'white'); b=io.BytesIO(); im.save(b,format='PNG')
    ip=ImageProcessor(TextProcessor(DetectorPipeline()))
    result,out=ip.analyze_bytes('logo.png',b.getvalue())
    assert result.sensitive is False
    assert Image.open(io.BytesIO(out)).size==(100,100)
