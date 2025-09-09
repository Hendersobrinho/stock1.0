"""
Formatação e validações de valores monetários em BRL (R$) e percentuais.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


TWO = Decimal("0.01")


def to_decimal(value: str | float | int) -> Decimal:
    """Converte para Decimal, aceitando string com vírgula ou ponto."""
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, (int, float)):
        d = Decimal(str(value))
    else:
        v = value.replace(" ", "").replace("R$", "").replace(".", "").replace(",", ".")
        d = Decimal(v)
    return d.quantize(TWO, rounding=ROUND_HALF_UP)


def br_money(value: str | float | int) -> str:
    """Formata valor como BRL com separadores: R$ 1.234,56."""
    d = to_decimal(value)
    # separador de milhar ponto, decimal vírgula
    s = f"{d:,.2f}"  # 1,234.56
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {s}"


def validate_positive(value: str | float | int, allow_zero: bool = False) -> Decimal:
    d = to_decimal(value)
    if (not allow_zero and d <= 0) or (allow_zero and d < 0):
        raise ValueError("Valor deve ser maior {} zero".format("ou igual a" if allow_zero else "que"))
    return d


def validate_percent(value: str | float | int) -> Decimal:
    try:
        d = to_decimal(value)
    except InvalidOperation:
        raise ValueError("Percentual inválido")
    if d < 0 or d > 100:
        raise ValueError("Percentual deve estar entre 0 e 100")
    return d


def round2(value: Decimal | float | int | str) -> Decimal:
    return to_decimal(value)


def br_number(value: str | float | int) -> str:
    """Formata número decimal no padrão brasileiro (duas casas, vírgula decimal)."""
    d = to_decimal(value)
    s = f"{d:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_datetime_br(iso_dt: str) -> str:
    """Converte uma string ISO (YYYY-MM-DD[ T]HH:MM:SS) para dd/mm/aaaa HH:MM."""
    from datetime import datetime
    try:
        # Aceita 'T' ou espaço como separador
        iso_dt = iso_dt.replace("T", " ")
        dt = datetime.fromisoformat(iso_dt)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_dt
