# 00 — Onde Começar (Guia de Leitura)

Este guia te conduz na ordem ideal para entender o projeto, do ponto de entrada até o banco.

Ordem sugerida e o que observar

1) app.py
- Ponto de entrada da GUI (Tkinter): cria janela, header, menu e telas.
- Observe: `App._on_login_success` adiciona abas (Produtos, Vendas, Pedidos, Relatórios).
- Dica: busque por `self.notebook.add` para ver a navegação.

2) views/sales_view.py (Tela de Vendas)
- Como o operador busca produtos, adiciona itens e finaliza a venda.
- Observe: `_update_suggestions` (busca por SKU/Nome/Categoria/Grupo) e `_finalize`.
- Mini roteiro: digite no campo de busca, dê duplo-clique em uma sugestão; preencha Qtd e Desconto%; finalize (F5) e veja a aba “Pedidos” abrir.

3) models/sale_model.py (Modelo de Venda)
- Persistência da venda em `sales`/`sale_items` e criação do “pedido lógico” em `orders`.
- Observe: `create_sale` calcula totais, grava itens e chama `OrderModel.create` (fora da transação).
- Mini roteiro: finalize uma venda e confira as tabelas com `scripts/check_db.py`.

4) models/product_model.py (Produtos)
- CRUD, validações, margem/markup e “grupo” (variantes).
- Observe: `search` com filtros SKU/Nome/Categoria/Grupo; `adjust_stock` registra movimento.

5) db.py (Banco de Dados)
- Conexão SQLite, criação de tabelas, migrações idempotentes.
- Observe: criação de `orders`, `order_items` e `stock_movements`.

6) utils/formatting.py e utils/exports.py
- Formatação BR (R$ 1.234,56) e exportação CSV (separador `;`).
- Observe: `br_money`, `fmt_datetime_br`, `export_csv`.

7) views/fulfillment_view.py / models/order_model.py (Pedidos)
- Fluxo de AGUARDANDO → PREPARADO → ENVIADO (baixa de estoque ao enviar).
- Observe: `FulfillmentFrame._advance` e `OrderModel.ship` (transação + checagem de estoque).

Mini roteiro prático

- Cadastre um produto (Produtos → Novo) e ajuste estoque se necessário.
- Faça uma venda (Vendas): busque, adicione item, finalize (F5).
- Veja o pedido em “Pedidos” e avance status (Ctrl+Enter). No “PREPARADO”, avance outra vez para ENVIADO (baixa estoque).
- Em Relatórios, defina o período e exporte Vendas e Pedidos (CSV).

Dica: use o script `scripts/check_db.py` para inspecionar o SQLite rapidamente.
