"""
Pacote utils: utilitários gerais usados no app.

Inclui:
- hash de senha didático (sha256 com SALT fixo)
- conversores/validadores simples (float e int não-negativos)

Outros utilitários especializados estão em submódulos:
- utils.formatting: BRL, percentuais e arredondamento (Decimal)
- utils.exports: exportação CSV
- utils.ids: geração de identificadores (sale_number)
"""

from __future__ import annotations

import hashlib


_STATIC_SALT = "stock_app_salt_v1"


def hash_password(password: str) -> str:
    """Retorna o hash sha256 da senha com SALT estático (didático)."""
    h = hashlib.sha256()
    h.update((_STATIC_SALT + password).encode("utf-8"))
    return h.hexdigest()


def ensure_positive_float(value_str: str) -> float:
    """Converte string para float >= 0, levantando ValueError com mensagem clara."""
    try:
        value = float(value_str.replace(",", "."))
    except ValueError:
        raise ValueError("Valor inválido: informe um número (ex.: 10.50)")
    if value < 0:
        raise ValueError("Valor deve ser maior ou igual a zero")
    return round(value, 2)


def ensure_non_negative_int(value_str: str) -> int:
    """Converte string para int >= 0, levantando ValueError com mensagem clara."""
    try:
        value = int(value_str)
    except ValueError:
        raise ValueError("Quantidade inválida: informe um inteiro (ex.: 5)")
    if value < 0:
        raise ValueError("Quantidade deve ser maior ou igual a zero")
    return value
