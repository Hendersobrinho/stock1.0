# 08 — Styleguide

PEP8 resumida
- Linhas até 88 colunas (aprox.).
- Nomes significativos: `product_id`, `sale_model`, `fulfillment_tab`.
- Funções com verbos: `create_product`, `refresh_table`.

Docstrings
- Módulos, classes e funções têm docstrings explicando o que/por que/como.
- Use exemplos mínimos quando fizer sentido.

Type hints
- Tipar parâmetros e retornos em funções públicas.

Estrutura de pastas
- `views/` (Tkinter), `models/` (regras e persistência), `utils/`, `db.py`, `app.py`.

Comentários pedagógicos
- Em blocos complexos, comente passo a passo com marcadores `(1)`, `(2)`.
