"""
Funções auxiliares de tempo: timestamps ISO e cálculos de SLA.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def hours_between(start_iso: str | None, end_iso: str | None) -> float | None:
    if not start_iso or not end_iso:
        return None
    try:
        a = datetime.fromisoformat(start_iso.replace("T", " "))
        b = datetime.fromisoformat(end_iso.replace("T", " "))
        return round((b - a).total_seconds() / 3600.0, 2)
    except Exception:
        return None


def compute_sla_deadline(created_iso: str, hours: int = 24) -> str:
    dt = datetime.fromisoformat(created_iso.replace("T", " "))
    return (dt + timedelta(hours=hours)).isoformat()

