"""
Camada de acesso a dados (SQLite) para o sistema de Controle de Estoque e Vendas.

Responsável por:
- Conexão com o banco (arquivo .db no diretório data/)
- Criação automática das tabelas (users, products, sales, sale_items)
- Fornecer conexões para os models
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime


class Database:
    """Abstrai as operações SQLite e garante criação de tabelas."""

    def __init__(self, db_path: str) -> None:
        # Garante que a pasta de dados exista
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        # Inicializa o banco e cria tabelas quando necessário
        self._init_db()

    # ---------------------- Utilitários internos ----------------------
    def _connect(self) -> sqlite3.Connection:
        """Retorna uma conexão SQLite com verificação de integridade ligada."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # acesso por nome de coluna
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Cria tabelas se não existirem e garante usuário padrão."""
        with closing(self._connect()) as conn, conn:
            # Migração de esquemas antigos (se necessário)
            self._migrate_schema(conn)
            # Tabela de usuários (login simples)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                );
                """
            )

            # Tabela de produtos (novo modelo)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT,
                    group_code TEXT,
                    cost_price REAL NOT NULL CHECK(cost_price > 0),
                    sale_price REAL NOT NULL CHECK(sale_price >= 0),
                    stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty >= 0),
                    min_stock INTEGER DEFAULT 0 CHECK(min_stock >= 0),
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )

            # Tabela de vendas (cabeçalho)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_number TEXT UNIQUE,
                    datetime TEXT NOT NULL,
                    total_gross REAL NOT NULL,
                    total_discount REAL NOT NULL,
                    total_net REAL NOT NULL,
                    items_count INTEGER NOT NULL,
                    notes TEXT
                );
                """
            )

            # Tabela de itens da venda
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    name TEXT NOT NULL,
                    qty INTEGER NOT NULL CHECK(qty > 0),
                    unit_price REAL NOT NULL CHECK(unit_price >= 0),
                    discount_percent REAL NOT NULL CHECK(discount_percent >= 0),
                    discount_value REAL NOT NULL CHECK(discount_value >= 0),
                    subtotal_gross REAL NOT NULL CHECK(subtotal_gross >= 0),
                    subtotal_net REAL NOT NULL CHECK(subtotal_net >= 0),
                    FOREIGN KEY(sale_id) REFERENCES sales(id),
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );
                """
            )

            # -------------------- Pedidos (orders) ---------------------
            # Cabeçalho de pedidos
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE NOT NULL,
                    customer_name TEXT,
                    customer_address TEXT,
                    customer_phone TEXT,
                    customer_email TEXT,
                    shipping_method TEXT,
                    shipping_cost REAL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    prepared_at TEXT,
                    ready_at TEXT,
                    shipped_at TEXT,
                    canceled_at TEXT,
                    total_gross REAL NOT NULL,
                    total_discount REAL NOT NULL,
                    total_net REAL NOT NULL,
                    notes TEXT
                );
                """
            )
            # Itens do pedido
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    name TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    discount_percent REAL NOT NULL DEFAULT 0,
                    discount_value REAL NOT NULL DEFAULT 0,
                    subtotal_gross REAL NOT NULL,
                    subtotal_net REAL NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(id),
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );
                """
            )
            # Índices úteis
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")

            # Movimentações de estoque (ledger)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    change INTEGER NOT NULL,
                    reason TEXT,
                    ref_type TEXT,
                    ref_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mov_product ON stock_movements(product_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mov_created ON stock_movements(created_at);")

            # Garante um usuário padrão caso a tabela esteja vazia
            cur = conn.execute("SELECT COUNT(*) AS n FROM users;")
            n_users = cur.fetchone()[0]
            if n_users == 0:
                # Inserimos usuário admin:admin (hash já deve vir calculado do chamador)
                from utils import hash_password

                conn.execute(
                    "INSERT INTO users (username, password_hash, criado_em) VALUES (?, ?, ?);",
                    ("admin", hash_password("admin"), datetime.utcnow().isoformat()),
                )
    # --------------------------- Usuários -----------------------------
    def validate_user(self, username: str, password_hash: str) -> bool:
        """Valida usuário/senha pelo hash informado."""
        with closing(self._connect()) as conn:
            cur = conn.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?;",
                (username, password_hash),
            )
            return cur.fetchone() is not None

    # --------------------------- Migrações ----------------------------
    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        """Migra esquemas antigos para o novo modelo quando detectados.

        - products: se não tem coluna 'sku', renomeia para products_legacy e recria copiando dados
        - sales: se contiver coluna 'produto_id', renomeia para sales_legacy
        """
        def columns_of(table: str) -> list[str]:
            try:
                cur = conn.execute(f"PRAGMA table_info({table});")
            except sqlite3.DatabaseError:
                return []
            return [r[1] for r in cur.fetchall()]

        # Products legacy?
        cols = columns_of("products")
        if cols and "sku" not in cols:
            try:
                conn.execute("ALTER TABLE products RENAME TO products_legacy;")
            except sqlite3.DatabaseError:
                pass
        # Ensure new columns on products
        cols = columns_of("products")
        if cols:
            if "group_code" not in cols:
                try:
                    conn.execute("ALTER TABLE products ADD COLUMN group_code TEXT;")
                except sqlite3.DatabaseError:
                    pass
            # Cria nova tabela products
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT,
                    cost_price REAL NOT NULL CHECK(cost_price > 0),
                    sale_price REAL NOT NULL CHECK(sale_price >= 0),
                    stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty >= 0),
                    min_stock INTEGER DEFAULT 0 CHECK(min_stock >= 0),
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )
            # Copia dados básicos da antiga
            now = datetime.utcnow().isoformat()
            try:
                cur = conn.execute("SELECT id, nome, categoria, preco, quantidade FROM products_legacy;")
                for r in cur.fetchall():
                    pid = int(r["id"]) if "id" in r.keys() else int(r[0])
                    nome = r["nome"] if "nome" in r.keys() else r[1]
                    categoria = r["categoria"] if "categoria" in r.keys() else r[2]
                    preco = float(r["preco"]) if "preco" in r.keys() else float(r[3])
                    qty = int(r["quantidade"]) if "quantidade" in r.keys() else int(r[4])
                    sku = f"LEG-{pid:06d}"
                    cost = preco if preco > 0 else 0.01
                    sale = preco
                    conn.execute(
                        """
                        INSERT INTO products (sku, name, category, cost_price, sale_price, stock_qty, min_stock, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (sku, nome, categoria, cost, sale, qty, 0, now, now),
                    )
            except sqlite3.DatabaseError:
                pass

        # Sales legacy?
        cols = columns_of("sales")
        if cols and "produto_id" in cols:
            try:
                conn.execute("ALTER TABLE sales RENAME TO sales_legacy;")
            except sqlite3.DatabaseError:
                pass

        # Orders: garantir colunas novas (ex.: customer_address)
        cols = columns_of("orders")
        if cols:
            if "customer_address" not in cols:
                try:
                    conn.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT;")
                except sqlite3.DatabaseError:
                    pass
