# 09 — Mapa de Eventos da Interface (Tkinter)

Vendas (views/sales_view.py)
- Entry de busca: `<KeyRelease>` → `_update_suggestions` → recarrega Listbox de sugestões.
- Listbox de sugestões: `<Double-Button-1>` → `_select_suggestion` → carrega SKU/Nome/Estoque/Preço.
- Qtd/Desc% (Entry): ao salvar item → `_add_item` → atualiza tabela e totais.
- Botão “Adicionar item”: `command=_add_item` → insere item no carrinho.
- Botão “Remover item (Del)”: `command=_remove_item` e `bind_all('<Delete>')` → remove item selecionado.
- Botão “Limpar venda”: `command=_clear_sale` → zera carrinho e campos.
- Botão “Aplicar desconto geral %”: `command=_apply_global_discount` → recalcula itens.
- Botão “Finalizar venda (F5)”: `command=_finalize` e `bind_all('<F5>')` → grava venda, cria pedido e navega para “Pedidos”.
- Atalhos extras: `bind_all('<F2>')` foca a busca.

Produtos (views/product_view.py)
- Botão “Novo”: `command=_clear_form` → limpa formulário.
- Botão “Salvar”: `command=_save` → valida e cria/atualiza produto.
- Botão “Excluir”: `command=_delete` → confirma e exclui.
- Botão “Ajustar Estoque”: `command=_adjust_stock` → pergunta delta/motivo e registra movimento.
- Filtros (SKU/Nome/Categoria/Grupo): `command=refresh_table` → recarrega listagem.
- Treeview: `<<TreeviewSelect>>` → `_on_select` → carrega dados no formulário.
- Reatividade: custos/preços → `_update_margin`; estoque/mínimo → `_update_stock_alert`.

Pedidos (views/fulfillment_view.py)
- Filtros: `command=refresh` → recarrega listagem por status/pesquisa.
- Treeview: `<<TreeviewSelect>>` → `_on_select` → carrega detalhes e totais.
- Botão “Avançar status (Ctrl+Enter)”: `command=_advance` e `bind_all('<Control-Return>')` → avança status; se PREPARADO, faz `ship()` com baixa de estoque.
- Botão “Cancelar (Del)”: `command=_cancel` e `bind_all('<Delete>')` → cancela o pedido (estágios iniciais).
- Atalhos rápidos: `F3` (AGUARDANDO), `F4/F6` (PREPARADO), `F7` (ENVIADO) → `_quick_filter`.

Relatórios (views/reports_view.py)
- Período: Combobox + Entries dd/mm/aaaa e botão “Aplicar” → `refresh` (faz SELECT com WHERE por período).
- Exportar Vendas/Itens/Pedidos: botões chamam `_export_sales_csv`, `_export_items_csv`, `_export_orders_csv`.
