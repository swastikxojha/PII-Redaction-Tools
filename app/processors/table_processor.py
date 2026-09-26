from __future__ import annotations

from app.detectors.base import DetectionContext
from app.processors.run_processor import apply_replacements_to_paragraph


class TableProcessor:
    def __init__(self, text_processor, pseudonymizer):
        self.text_processor=text_processor
        self.pseudonymizer=pseudonymizer

    def process(self, tables, stats):
        for ti, table in enumerate(tables):
            for ri, row in enumerate(table.rows):
                for ci, cell in enumerate(row.cells):
                    for pi, paragraph in enumerate(cell.paragraphs):
                        text=paragraph.text
                        if not text.strip():
                            continue
                        context=DetectionContext(location="table", block_id=f"table{ti}:r{ri}:c{ci}:p{pi}")
                        entities=self.text_processor.detect(text, context)
                        stats.add_entities(entities)
                        replacements=[(e,self.pseudonymizer.replacement_for(e)) for e in entities]
                        apply_replacements_to_paragraph(paragraph, replacements)
