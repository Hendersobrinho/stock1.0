"""
Módulo: models/product_model.py

Visão geral
    Regras de negócio de produtos: CRUD, validações (preços/estoque),
    métricas (margem/markup), busca por SKU/Nome/Categoria/Grupo e ajuste de estoque.

Quando usar/editar
    - Ao alterar regras de cadastro/validação.
    - Para adicionar novos filtros de busca ou campos (ex.: grupo).

Como conversa com outros módulos
    - Usa `db.Database` para conectar ao SQLite.
    - Utiliza `utils.formatting.round2` para cálculos com 2 casas decimais.

Mapa rápido
    - Product (dataclass): espelha a linha da tabela `products`.
    - ProductModel.create/update/delete/get/search/list_all: operações de produto.
    - ProductModel.adjust_stock: ajusta estoque e registra em `stock_movements`.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from db import Database
from utils.formatting import validate_positive, round2


@dataclass
class Product:
    id: int
    sku: str
    name: str
    category: str | None
    group_code: str | None
    cost_price: float
    sale_price: float
    stock_qty: int
    min_stock: int

    @property
    def margin_unit(self) -> float:
        return float(round2(self.sale_price) - round2(self.cost_price))

    @property
    def markup_percent(self) -> float:
        if self.cost_price == 0:
            return 0.0
        return float((round2(self.sale_price) / round2(self.cost_price) - 1) * 100)


class ProductModel:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --------------------------- CRUD ---------------------------
    def create(self, sku: str, name: str, category: str | None, cost_price: str | float | int,
               sale_price: str | float | int, stock_qty: int, min_stock: int,
               group_code: str | None = None) -> int:
        sku = sku.strip().upper()
        name = name.strip()
        category = (category or "").strip() or None
        group_code = (group_code or "").strip() or None
        if not sku or not name:
            raise ValueError("SKU e Nome são obrigatórios")

        cost = float(validate_positive(cost_price, allow_zero=False))
        sale = float(validate_positive(sale_price, allow_zero=True))
        if sale < cost:
            raise ValueError("Preço de venda não pode ser menor que o preço de custo")
        if stock_qty < 0 or min_stock < 0:
            raise ValueError("Estoque e estoque mínimo devem ser >= 0")

        with closing(self.db._connect()) as conn, conn:
            # SKU único
            cur = conn.execute("SELECT id FROM products WHERE sku = ?;", (sku,))
            if cur.fetchone():
                raise ValueError("SKU já cadastrado")
            now = datetime.utcnow().isoformat()
            cur = conn.execute(
                """
                INSERT INTO products (sku, name, category, group_code, cost_price, sale_price, stock_qty, min_stock, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (sku, name, category, group_code, cost, sale, stock_qty, min_stock, now, now),
            )
            return int(cur.lastrowid)

    def update(self, product_id: int, sku: str, name: str, category: str | None,
               cost_price: str | float | int, sale_price: str | float | int,
               stock_qty: int, min_stock: int, group_code: str | None = None) -> None:
        sku = sku.strip().upper()
        name = name.strip()
        category = (category or "").strip() or None
        group_code = (group_code or "").strip() or None
        if not sku or not name:
            raise ValueError("SKU e Nome são obrigatórios")
        cost = float(validate_positive(cost_price, allow_zero=False))
        sale = float(validate_positive(sale_price, allow_zero=True))
        if sale < cost:
            raise ValueError("Preço de venda não pode ser menor que o preço de custo")
        if stock_qty < 0 or min_stock < 0:
            raise ValueError("Estoque e estoque mínimo devem ser >= 0")

        with closing(self.db._connect()) as conn, conn:
            cur = conn.execute("SELECT id FROM products WHERE sku = ? AND id <> ?;", (sku, product_id))
            if cur.fetchone():
                raise ValueError("SKU já cadastrado em outro produto")
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                UPDATE products
                   SET sku=?, name=?, category=?, group_code=?, cost_price=?, sale_price=?, stock_qty=?, min_stock=?, updated_at=?
                 WHERE id=?;
                """,
                (sku, name, category, group_code, cost, sale, stock_qty, min_stock, now, product_id),
            )

    def delete(self, product_id: int) -> None:
        with closing(self.db._connect()) as conn, conn:
            conn.execute("DELETE FROM products WHERE id=?;", (product_id,))

    # --------------------------- Consultas -----------------------
    def get(self, product_id: int) -> Optional[Product]:
        with closing(self.db._connect()) as conn:
            cur = conn.execute("SELECT * FROM products WHERE id=?;", (product_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Product(
                id=r["id"], sku=r["sku"], name=r["name"], category=r["category"], group_code=r["group_code"],
                cost_price=float(r["cost_price"]), sale_price=float(r["sale_price"]),
                stock_qty=int(r["stock_qty"]), min_stock=int(r["min_stock"]),
            )

    def search(self, sku: str = "", name: str = "", category: str = "", group_code: str = "") -> list[Product]:
        sku = sku.strip().upper()
        name = name.strip()
        category = category.strip()
        group_code = group_code.strip()
        where = []
        params: list[str] = []
        if sku:
            where.append("sku LIKE ?")
            params.append(f"%{sku}%")
        if name:
            where.append("name LIKE ?")
            params.append(f"%{name}%")
        if category:
            where.append("category LIKE ?")
            params.append(f"%{category}%")
        if group_code:
            where.append("COALESCE(group_code,'') LIKE ?")
            params.append(f"%{group_code}%")
        sql = "SELECT * FROM products"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY name ASC;"
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            res: list[Product] = []
            for r in rows:
                res.append(
                    Product(
                        id=r["id"], sku=r["sku"], name=r["name"], category=r["category"], group_code=r["group_code"],
                        cost_price=float(r["cost_price"]), sale_price=float(r["sale_price"]),
                        stock_qty=int(r["stock_qty"]), min_stock=int(r["min_stock"]),
                    )
                )
            return res

    def list_all(self) -> list[Product]:
        return self.search()

    # --------------------- Ajuste de estoque ----------------------
    def adjust_stock(self, product_id: int, delta: int, reason: str) -> None:
        if delta == 0:
            return
        with closing(self.db._connect()) as conn, conn:
            # Busca estoque atual
            cur = conn.execute("SELECT stock_qty FROM products WHERE id=?;", (product_id,))
            r = cur.fetchone()
            if not r:
                raise ValueError("Produto inexistente")
            new_qty = int(r[0]) + int(delta)
            if new_qty < 0:
                raise ValueError("Ajuste resultaria em estoque negativo")
            conn.execute("UPDATE products SET stock_qty = ?, updated_at = ? WHERE id=?;", (new_qty, datetime.utcnow().isoformat(), product_id))
            # Movimento de estoque
            conn.execute(
                """
                INSERT INTO stock_movements (product_id, change, reason, ref_type, ref_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (product_id, int(delta), reason or "Ajuste manual", "ADJUST", None, datetime.utcnow().isoformat()),
            )
