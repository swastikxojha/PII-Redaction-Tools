from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from docx.text.run import Run
from docx.oxml.ns import qn


@dataclass(frozen=True)
class RunRange:
    run: Run
    start: int
    end: int


def get_run_ranges(paragraph) -> tuple[str, list[RunRange]]:
    ranges=[]
    cursor=0
    for run in paragraph.runs:
        txt=run.text or ""
        ranges.append(RunRange(run,cursor,cursor+len(txt)))
        cursor += len(txt)
    return ''.join(r.run.text or '' for r in ranges), ranges


def _run_index_for_char(ranges: list[RunRange], idx: int) -> int:
    if not ranges:
        return 0
    for i,rr in enumerate(ranges):
        if rr.start <= idx < rr.end:
            return i
    return len(ranges)-1


def _new_segments(text: str, ranges: list[RunRange], replacements):
    """Return (source_run_index, generated_text) chunks for formatting-preserving rebuild."""
    replacements=sorted(replacements, key=lambda x:x[0].start)
    pieces=[]
    cursor=0
    for entity, replacement in replacements:
        if entity.start < cursor:
            continue
        if cursor < entity.start:
            plain=text[cursor:entity.start]
            if plain:
                pieces.append((_run_index_for_char(ranges,cursor),plain))
        style_idx=_run_index_for_char(ranges, entity.start)
        pieces.append((style_idx,replacement))
        cursor=entity.end
    if cursor < len(text):
        pieces.append((_run_index_for_char(ranges,cursor),text[cursor:]))
    # Merge adjacent chunks using the same source run style.
    merged=[]
    for idx,chunk in pieces:
        if not chunk: continue
        if merged and merged[-1][0]==idx:
            merged[-1]=(idx,merged[-1][1]+chunk)
        else:
            merged.append((idx,chunk))
    return merged


def _clear_run(run: Run):
    # Keep run properties; clear content via public API.
    run.text=''


def apply_replacements_to_paragraph(paragraph, replacements):
    """Apply all spans against the original paragraph text in one pass.

    Most prospectus text is represented by ordinary Word runs. For those paragraphs we rebuild
    the run sequence while cloning the source run formatting. Complex paragraphs containing
    hyperlinks/drawings are left alone rather than risking structural damage.
    """
    text, ranges=get_run_ranges(paragraph)
    if not replacements or not text or not ranges:
        return

    # Avoid changing paragraphs that contain non-run XML siblings such as inline drawings or hyperlinks.
    p_xml=paragraph._p
    complex_children=p_xml.xpath('./w:hyperlink | ./w:drawing | ./w:object')
    if complex_children:
        # Conservative fallback for plain run boundaries.
        _apply_simple_descending(paragraph, replacements)
        return

    segments=_new_segments(text,ranges,replacements)
    if not segments:
        return

    # Remove existing run elements, retaining paragraph properties and other structural children.
    for rr in ranges:
        try:
            p_xml.remove(rr.run._r)
        except ValueError:
            pass

    # Recreate runs using the formatting of the original source run.
    for style_idx, segment_text in segments:
        template=deepcopy(ranges[style_idx].run._r)
        run=Run(template, paragraph)
        run.text=segment_text
        p_xml.append(template)


def _apply_simple_descending(paragraph, replacements):
    """Best-effort fallback for complex paragraphs; updates offsets after each edit."""
    text,ranges=get_run_ranges(paragraph)
    # Only apply edits in reverse order. Recompute run ranges each time.
    for entity,replacement in sorted(replacements,key=lambda x:x[0].start,reverse=True):
        text,ranges=get_run_ranges(paragraph)
        s,e=entity.start,entity.end
        start_rr=end_rr=None
        for rr in ranges:
            if rr.start <= s < rr.end:
                start_rr=rr
            if rr.start < e <= rr.end:
                end_rr=rr
            if start_rr and end_rr: break
        if start_rr is None: continue
        if end_rr is None: end_rr=start_rr
        start_text=start_rr.run.text or ''
        end_text=end_rr.run.text or ''
        start_local=s-start_rr.start
        end_local=e-end_rr.start
        if start_rr is end_rr:
            start_rr.run.text=start_text[:start_local]+replacement+start_text[end_local:]
        else:
            start_rr.run.text=start_text[:start_local]+replacement
            sr=ranges.index(start_rr); er=ranges.index(end_rr)
            for rr in ranges[sr+1:er]: rr.run.text=''
            end_rr.run.text=end_text[end_local:]
