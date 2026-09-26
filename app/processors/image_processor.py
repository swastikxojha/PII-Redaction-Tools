from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from app.detectors.base import DetectionContext
from app.processors.ocr_processor import OCRProcessor


SENSITIVE_IMAGE_HINTS=(
    "permanent account number",
    "income tax",
    "pan card",
    "unique identification authority",
    "aadhaar",
    "government of india",
    "date of birth",
    "dob",
    "father",
    "signature",
)


@dataclass
class ImageResult:
    media_name: str
    width: int
    height: int
    ocr_text: str
    sensitive: bool
    reasons: list[str]


class ImageProcessor:
    """OCR and conservative visual redaction for embedded image media."""

    def __init__(self, text_processor, threshold: float = 0.80):
        self.text_processor=text_processor
        self.threshold=threshold
        self.ocr_processor=OCRProcessor()

    def analyze_bytes(self, media_name: str, data: bytes) -> tuple[ImageResult, bytes]:
        try:
            image=Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            return ImageResult(media_name,0,0,"",False,["unreadable-image"]), data

        ocr_result=self.ocr_processor.extract(image)
        ocr=ocr_result.data
        text=ocr_result.text
        low=text.casefold()
        reasons=[]
        for hint in SENSITIVE_IMAGE_HINTS:
            if hint in low:
                reasons.append(f"ocr:{hint}")
        # Structured detector catches exact identifier patterns the OCR happens to recognize.
        try:
            ents=self.text_processor.detect(text, DetectionContext(location="image", block_id=media_name))
        except Exception:
            ents=[]
        pii_types={e.type.value for e in ents}
        if pii_types:
            reasons.append("pii-detector:" + ",".join(sorted(pii_types)))
        sensitive=bool(reasons)
        if sensitive:
            output=self._redact_image(image, "PERSONAL DATA IMAGE REDACTED")
        else:
            # Even for non-sensitive images, re-encode losslessly where possible to keep media clean.
            output=io.BytesIO()
            image.save(output, format="PNG")
            output=output.getvalue()
        return ImageResult(media_name,image.width,image.height,text,sensitive,reasons), output

    @staticmethod
    def _redact_image(image: Image.Image, label: str) -> bytes:
        # Full-image redaction is intentional for identity-document images: partial OCR can miss text,
        # signatures, QR payloads, or visual identifiers. Preserve canvas dimensions to avoid layout shifts.
        im=image.copy()
        draw=ImageDraw.Draw(im)
        draw.rectangle([0,0,im.width-1,im.height-1], fill=(230,230,230), outline=(80,80,80), width=max(2,im.width//200))
        draw.rectangle([im.width*0.08, im.height*0.35, im.width*0.92, im.height*0.65], fill=(70,70,70))
        # Wrap and size the notice so it never clips beyond the image bounds.
        import textwrap
        font_path="DejaVuSans-Bold.ttf"
        size=max(14, min(42, im.width//24))
        while size >= 12:
            try:
                font=ImageFont.truetype(font_path, size)
            except Exception:
                font=ImageFont.load_default()
            max_width=int(im.width*0.84)
            words=label.split()
            lines=[]; current=""
            for word in words:
                candidate=(current+" "+word).strip()
                if draw.textbbox((0,0),candidate,font=font)[2] <= max_width:
                    current=candidate
                else:
                    if current: lines.append(current)
                    current=word
            if current: lines.append(current)
            widths=[draw.textbbox((0,0),line,font=font)[2] for line in lines]
            if max(widths, default=0) <= max_width:
                break
            size -= 2
        line_h=max(18, size+8)
        total_h=line_h*len(lines)
        y=(im.height-total_h)/2
        for line,w in zip(lines,widths):
            x=(im.width-w)/2
            draw.text((x,y), line, fill=(255,255,255), font=font)
            y += line_h
        out=io.BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()
