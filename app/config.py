from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    confidence_threshold: float = 0.80
    seed: int = 20250925
    enable_image_ocr: bool = True


ROOT=Path(__file__).resolve().parents[1]
INPUT_DIR=ROOT/'input'
OUTPUT_DIR=ROOT/'output'
EVAL_DIR=ROOT/'evaluation'
DEFAULT_INPUT=INPUT_DIR/'Red Herring Prospectus.docx'
DEFAULT_OUTPUT=OUTPUT_DIR/'redacted_output.docx'
