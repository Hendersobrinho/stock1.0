"""
Exportação de dados para CSV.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence


def export_csv(file_path: str | Path, headers: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(headers)
        for r in rows:
            w.writerow(r)

