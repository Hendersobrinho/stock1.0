# 03 — Guia rápido de SQLite

Abrindo o .db
- O arquivo do banco fica em `data/estoque.db`.
- Use ferramentas como DB Browser for SQLite, DBeaver ou o módulo `sqlite3` do Python.

Comandos básicos
- Criar tabela:
  ```sql
  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL
  );
  ```
- Inserir:
  ```sql
  INSERT INTO products (sku) VALUES ('ABC-001');
  ```
- Buscar:
  ```sql
  SELECT * FROM products ORDER BY id DESC;
  ```
- Atualizar/Excluir:
  ```sql
  UPDATE products SET sku='ABC-002' WHERE id=1;
  DELETE FROM products WHERE id=1;
  ```

Índices
- Melhoram a velocidade de buscas. Ex.: `CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);`

Precisão monetária
- Tabelas usam `REAL` por simplicidade.
- No Python, usamos `Decimal` (utils/formatting.round2) para somas e arredondamentos com 2 casas (half-up), reduzindo erros de ponto flutuante.
