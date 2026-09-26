from __future__ import annotations

from dataclasses import dataclass
from PIL import Image
import pytesseract
from pytesseract import Output


@dataclass
class OCRResult:
    text: str
    data: dict


class OCRProcessor:
    """Small adapter around pytesseract so OCR remains independently testable."""

    def __init__(self, config: str = "--psm 6", lang: str | None = None):
        self.config = config
        self.lang = lang

    def extract(self, image: Image.Image) -> OCRResult:
        kwargs = {"output_type": Output.DICT, "config": self.config}
        if self.lang:
            kwargs["lang"] = self.lang
        data = pytesseract.image_to_data(image, **kwargs)
        words = [t.strip() for t in data.get("text", []) if t and t.strip()]
        return OCRResult(" ".join(words), data)
