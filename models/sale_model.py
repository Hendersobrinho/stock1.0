"""
Model de Vendas: criação de venda, inserção de itens, totais e baixa de estoque.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List, Tuple

from db import Database
from utils.formatting import round2, validate_percent
from utils.ids import next_sale_number


@dataclass
class SaleItemInput:
    product_id: int
    sku: str
    name: str
    qty: int
    unit_price: Decimal
    discount_percent: Decimal  # 0..100


class SaleModel:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_sale(self, items: List[SaleItemInput], notes: str = "", prefix: str = "HND",
                    customer_name: str | None = None, customer_email: str | None = None,
                    customer_address: str | None = None, shipping_method: str | None = None,
                    shipping_cost: float | int | None = 0.0) -> int:
        """Cria uma venda completa com itens (sem baixar estoque aqui).

        Regras:
        - Valida percentuais e quantidades
        - Calcula totais
        - Gera sale_number sequencial
        - Persiste em sales e sale_items
        - Atualiza estoque (stock_qty -= qty)
        """
        if not items:
            raise ValueError("A venda deve conter ao menos um item")

        # Calcula totais em Decimal para precisão
        total_gross = Decimal("0")
        total_discount = Decimal("0")
        total_net = Decimal("0")

        # Pré-validação e leitura de estoque
        with closing(self.db._connect()) as conn:
            # Verifica estoques
            for it in items:
                if it.qty <= 0:
                    raise ValueError("Quantidade deve ser >= 1")
                validate_percent(it.discount_percent)
                cur = conn.execute("SELECT stock_qty FROM products WHERE id=?;", (it.product_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Produto inexistente: {it.sku}")
                stock = int(row[0])
                if it.qty > stock:
                    raise ValueError(f"Estoque insuficiente para {it.sku}")

        # Cálculos
        per_item_values: List[Tuple[Decimal, Decimal, Decimal]] = []
        for it in items:
            ug = round2(it.unit_price)
            q = Decimal(it.qty)
            subtotal_gross = round2(ug * q)
            dperc = round2(it.discount_percent) / Decimal(100)
            discount_value = round2(subtotal_gross * dperc)
            subtotal_net = round2(subtotal_gross - discount_value)
            per_item_values.append((subtotal_gross, discount_value, subtotal_net))
            total_gross += subtotal_gross
            total_discount += discount_value
            total_net += subtotal_net

        total_gross = round2(total_gross)
        total_discount = round2(total_discount)
        total_net = round2(total_net)

        # Persistência (venda)
        with closing(self.db._connect()) as conn, conn:
            sale_number = next_sale_number(self.db, prefix=prefix)
            cur = conn.execute(
                """
                INSERT INTO sales (sale_number, datetime, total_gross, total_discount, total_net, items_count, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    sale_number,
                    datetime.utcnow().isoformat(),
                    float(total_gross),
                    float(total_discount),
                    float(total_net),
                    len(items),
                    notes,
                ),
            )
            sale_id = int(cur.lastrowid)

            # Itens
            for it, (subtotal_gross, discount_value, subtotal_net) in zip(items, per_item_values):
                conn.execute(
                    """
                    INSERT INTO sale_items (
                        sale_id, product_id, sku, name, qty, unit_price, discount_percent, discount_value, subtotal_gross, subtotal_net
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        sale_id,
                        it.product_id,
                        it.sku,
                        it.name,
                        it.qty,
                        float(round2(it.unit_price)),
                        float(round2(it.discount_percent)),
                        float(discount_value),
                        float(subtotal_gross),
                        float(subtotal_net),
                    ),
                )

        # Integração: cria pedido 'AGUARDANDO' a partir desta venda (fora da transação da venda)
        try:
            from models.order_model import OrderModel, OrderItemInput  # import local para evitar ciclo
            om = OrderModel(self.db)
            order_items = [
                OrderItemInput(
                    product_id=it.product_id,
                    sku=str(it.sku),
                    name=str(it.name),
                    qty=int(it.qty),
                    unit_price=float(round2(it.unit_price)),
                    discount_percent=float(round2(it.discount_percent)),
                )
                for it in items
            ]
            om.create(
                customer_name=customer_name or "Cliente",
                customer_phone=None,
                customer_email=customer_email,
                shipping_method=shipping_method or "Correios",
                shipping_cost=float(shipping_cost or 0),
                items=order_items,
                customer_address=customer_address,
                notes=f"Gerado automaticamente da venda #{sale_id}",
            )
        except Exception:
            # Integração é opcional; se falhar, mantemos a venda registrada
            pass

        return sale_id
