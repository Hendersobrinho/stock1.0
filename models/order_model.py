"""
Model de Pedidos (orders): criação a partir de vendas, itens, transições de status
e baixa de estoque no envio.

Política de estoque:
- Criar pedido NÃO baixa estoque (apenas reserva lógica, opcional futura).
- Ao mudar para ENVIADO: baixa estoque (stock_qty -= qty) dentro de transação.
- Ao CANCELAR: não altera estoque (se já foi ENVIADO, manter histórico e não reverter automaticamente).

Status e transições:
- AGUARDANDO PREPARO -> EM PREPARO -> PRONTO PARA ENVIO -> ENVIADO
- Qualquer um dos três primeiros -> CANCELADO

Timestamps:
- prepared_at, ready_at, shipped_at, canceled_at são marcados quando a transição ocorre.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from db import Database
from utils.ids import next_order_number
from utils.time import now_iso


# Status simplificados: AGUARDANDO -> PREPARADO -> ENVIADO (CANCELADO opcional)
ALLOWED_TRANSITIONS = {
    "AGUARDANDO": {"PREPARADO", "CANCELADO"},
    "PREPARADO": {"ENVIADO", "CANCELADO"},
}


@dataclass
class OrderItemInput:
    product_id: int
    sku: str
    name: str
    qty: int
    unit_price: float
    discount_percent: float


class OrderModel:
    def __init__(self, db: Database) -> None:
        self.db = db

    # -------------------------- Criação --------------------------
    def create(self, customer_name: str, customer_phone: str | None, customer_email: str | None,
               shipping_method: str | None, shipping_cost: float, items: list[OrderItemInput],
               customer_address: str | None = None,
               notes: str = "") -> int:
        if not items:
            raise ValueError("Pedido deve conter ao menos um item")
        order_number = next_order_number(self.db)

        # Calcula totais
        total_gross = 0.0
        total_discount = 0.0
        total_net = 0.0
        for it in items:
            subtotal_gross = round(it.unit_price * it.qty, 2)
            disc_value = round(subtotal_gross * (it.discount_percent / 100.0), 2)
            subtotal_net = round(subtotal_gross - disc_value, 2)
            total_gross += subtotal_gross
            total_discount += disc_value
            total_net += subtotal_net
        total_net = round(total_net + float(shipping_cost or 0), 2)

        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute(
                """
                INSERT INTO orders (
                    order_number, customer_name, customer_address, customer_phone, customer_email, shipping_method, shipping_cost,
                    status, created_at, total_gross, total_discount, total_net, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'AGUARDANDO', ?, ?, ?, ?, ?);
                """,
                (
                    order_number,
                    customer_name,
                    customer_address,
                    customer_phone,
                    customer_email,
                    shipping_method,
                    float(shipping_cost or 0),
                    now_iso(),
                    round(total_gross, 2),
                    round(total_discount, 2),
                    round(total_net, 2),
                    notes,
                ),
            )
            order_id = int(cur.lastrowid)

            for it in items:
                subtotal_gross = round(it.unit_price * it.qty, 2)
                disc_value = round(subtotal_gross * (it.discount_percent / 100.0), 2)
                subtotal_net = round(subtotal_gross - disc_value, 2)
                conn.execute(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, sku, name, qty, unit_price, discount_percent, discount_value, subtotal_gross, subtotal_net
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        order_id,
                        it.product_id,
                        it.sku,
                        it.name,
                        it.qty,
                        round(float(it.unit_price), 2),
                        round(float(it.discount_percent), 2),
                        disc_value,
                        subtotal_gross,
                        subtotal_net,
                    ),
                )

            return order_id

    def create_from_sale(self, sale_id: int) -> Optional[int]:
        """Cria um pedido a partir de uma venda já registrada.

        Nota: aqui assumimos que 'sales' e 'sale_items' existem conforme implementação local.
        """
        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute(
                "SELECT total_gross, total_discount, total_net FROM sales WHERE id = ?;",
                (sale_id,),
            )
            s = cur.fetchone()
            if not s:
                return None
            cur = conn.execute(
                "SELECT product_id, sku, name, qty, unit_price, discount_percent FROM sale_items WHERE sale_id = ?;",
                (sale_id,),
            )
            rows = cur.fetchall()
            if not rows:
                return None
            items = [
                OrderItemInput(
                    product_id=r["product_id"],
                    sku=r["sku"],
                    name=r["name"],
                    qty=r["qty"],
                    unit_price=float(r["unit_price"]),
                    discount_percent=float(r["discount_percent"]),
                )
                for r in rows
            ]

        # Cliente e frete não são capturados na venda atual; usamos placeholders.
        return self.create(
            customer_name="Cliente da Venda",
            customer_phone=None,
            customer_email=None,
            shipping_method="Correios",
            shipping_cost=0.0,
            items=items,
            notes=f"Criado a partir da venda #{sale_id}",
        )

    # ----------------------- Transições/Status ----------------------
    def advance_status(self, order_id: int) -> str:
        """Avança o status do pedido para o próximo estágio permitido.

        Retorna o novo status.
        """
        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute("SELECT status FROM orders WHERE id = ?;", (order_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Pedido inexistente")
            status = row["status"]
            if status not in ALLOWED_TRANSITIONS:
                raise ValueError("Não é possível avançar este status")
            next_map = {
                "AGUARDANDO": "PREPARADO",
                "PREPARADO": "ENVIADO",
            }
            new_status = next_map[status]
            self._set_status(conn, order_id, status, new_status)
            return new_status

    def cancel(self, order_id: int) -> None:
        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute("SELECT status FROM orders WHERE id = ?;", (order_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Pedido inexistente")
            status = row["status"]
            if status not in ("AGUARDANDO", "PREPARADO"):
                raise ValueError("Pedido não pode ser cancelado neste status")
            self._set_status(conn, order_id, status, "CANCELADO")

    def ship(self, order_id: int) -> None:
        """Marca como ENVIADO e baixa estoque. Transação atômica."""
        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute("SELECT status FROM orders WHERE id = ?;", (order_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("Pedido inexistente")
            status = row["status"]
            if status != "PREPARADO":
                raise ValueError("Somente pedidos 'PREPARADO' podem ser enviados")

            # Verifica itens e estoque
            cur = conn.execute("SELECT product_id, qty FROM order_items WHERE order_id = ?;", (order_id,))
            items = cur.fetchall()
            if not items:
                raise ValueError("Pedido sem itens")
            for it in items:
                cur2 = conn.execute("SELECT stock_qty FROM products WHERE id = ?;", (it["product_id"],))
                r = cur2.fetchone()
                if not r or int(r["stock_qty"]) < int(it["qty"]):
                    raise ValueError("Estoque insuficiente para envio")

            # Baixa estoque
            for it in items:
                conn.execute(
                    "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?;",
                    (int(it["qty"]), int(it["product_id"]))
                )
                # Registra movimentação
                conn.execute(
                    """
                    INSERT INTO stock_movements (product_id, change, reason, ref_type, ref_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (int(it["product_id"]), -int(it["qty"]), "Envio de pedido", "ORDER_SHIP", order_id, now_iso()),
                )

            # Atualiza status para ENVIADO
            self._set_status(conn, order_id, status, "ENVIADO")

    def _set_status(self, conn, order_id: int, old: str, new: str) -> None:
        if old == new:
            return
        if old in ALLOWED_TRANSITIONS and new not in ALLOWED_TRANSITIONS[old] and new != "ENVIADO":
            # (ENVIADO) é tratado por ship()
            raise ValueError("Transição de status inválida")
        ts_field = None
        if new == "PREPARADO":
            ts_field = "prepared_at"
        elif new == "ENVIADO":
            ts_field = "shipped_at"
        elif new == "CANCELADO":
            ts_field = "canceled_at"
        sets = ["status = ?"]
        params: list[object] = [new]
        if ts_field:
            sets.append(f"{ts_field} = ?")
            params.append(now_iso())
        params.append(order_id)
        conn.execute(f"UPDATE orders SET {', '.join(sets)} WHERE id = ?;", params)

    # -------------------------- Consultas --------------------------
    def list(self, status: str | None = None, search: str | None = None) -> list[dict]:
        sql = "SELECT * FROM orders"
        where = []
        params: list[object] = []
        if status:
            where.append("status = ?")
            params.append(status)
        if search:
            where.append("(order_number LIKE ? OR customer_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC;"
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
        return rows

    def get_items(self, order_id: int) -> list[dict]:
        with closing(self.db._connect()) as conn:
            cur = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id;", (order_id,))
            return [dict(r) for r in cur.fetchall()]

    # ---------------------- Dados de Exemplo ----------------------
    def seed_examples(self) -> None:
        """Cria 5–10 pedidos de exemplo, se desejar. Usa primeiros produtos cadastrados.

        Por segurança, não roda automaticamente. Deve ser invocada pelo usuário.
        """
        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute("SELECT COUNT(*) FROM orders;")
            if int(cur.fetchone()[0]) > 0:
                return
            cur = conn.execute("SELECT id, sku, name, sale_price FROM products ORDER BY id LIMIT 5;")
            prods = cur.fetchall()
            if not prods:
                return
            # Monta 5 pedidos simples
            statuses = [
                "AGUARDANDO PREPARO",
                "EM PREPARO",
                "PRONTO PARA ENVIO",
                "ENVIADO",
                "CANCELADO",
            ]
            for i, st in enumerate(statuses):
                it = prods[i % len(prods)]
                items = [
                    OrderItemInput(
                        product_id=it["id"], sku=it["sku"], name=it["name"], qty=1 + (i % 3), unit_price=float(it["sale_price"]), discount_percent=0.0
                    )
                ]
                oid = self.create(
                    customer_name=f"Cliente {i+1}", customer_phone=None, customer_email=None,
                    shipping_method="Correios", shipping_cost=0.0, items=items,
                    notes="Exemplo"
                )
                if st == "EM PREPARO":
                    self.advance_status(oid)
                elif st == "PRONTO PARA ENVIO":
                    self.advance_status(oid)
                    self.advance_status(oid)
                elif st == "ENVIADO":
                    self.advance_status(oid)
                    self.advance_status(oid)
                    self.ship(oid)
                elif st == "CANCELADO":
                    self.cancel(oid)
