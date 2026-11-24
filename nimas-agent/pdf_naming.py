"""Conventions shared by PDF intake and legacy-project migration."""
import re
from pathlib import Path

RANGE_RE = re.compile(r"(?:^|[_\- ])([0-9]{1,4}|[ivxlcdm]+)[_\-]([0-9]{1,4}|[ivxlcdm]+)(?:[_\- .]|$)", re.I)

def source_page_range(filename: str):
    """Return the printed/page-label range encoded in a PDF filename."""
    stem = Path(filename).stem
    matches = list(RANGE_RE.finditer(stem))
    if not matches:
        return None
    values = matches[-1].groups()
    def parse(value):
        return int(value) if value.isdigit() else value.lower()
    return [parse(values[0]), parse(values[1])]

def physical_page_range(filename: str, page_count: int):
    """Return the 1-based physical PDF range, preserving LP's printed zero."""
    source = source_page_range(filename)
    if not source:
        return [1, page_count]
    if all(isinstance(value, int) for value in source):
        return [1, page_count]
    return [1, page_count]
