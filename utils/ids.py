"""
Geração de identificadores (ex.: sale_number sequencial AAA-000001).
"""

from __future__ import annotations

import re
from contextlib import closing
from typing import Tuple

from db import Database


PAT = re.compile(r"^([A-Z]{3})-(\d{6})$")


def next_sale_number(db: Database, prefix: str = "HND") -> str:
    """Gera próximo número de venda sequencial com prefixo de 3 letras.

    Formato: XXX-000001
    """
    if not re.fullmatch(r"[A-Z]{3}", prefix.upper()):
        raise ValueError("Prefixo deve ter 3 letras maiúsculas")
    with closing(db._connect()) as conn:
        cur = conn.execute(
            "SELECT sale_number FROM sales WHERE sale_number LIKE ? ORDER BY id DESC LIMIT 1;",
            (f"{prefix}-%",),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return f"{prefix}-000001"
        m = PAT.match(row[0])
        if not m:
            return f"{prefix}-000001"
        num = int(m.group(2)) + 1
        return f"{prefix}-{num:06d}"


def next_order_number(db: Database, prefix: str = "HND-ORD") -> str:
    """Gera próximo número de pedido sequencial.

    Formato: HHH-XXX-000001 (prefixo com hífen é aceito)
    """
    with closing(db._connect()) as conn:
        cur = conn.execute(
            "SELECT order_number FROM orders WHERE order_number LIKE ? ORDER BY id DESC LIMIT 1;",
            (f"{prefix}-%",),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return f"{prefix}-000001"
        try:
            suffix = int(row[0].rsplit("-", 1)[1]) + 1
        except Exception:
            suffix = 1
        return f"{prefix}-{suffix:06d}"
