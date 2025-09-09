# 04 — Guia rápido de Tkinter

Widgets principais usados
- Frame (ttk.Frame): organização do layout em blocos.
- Label (ttk.Label): textos e títulos.
- Entry (ttk.Entry): campos de texto.
- Button (ttk.Button): ações; `command=...` aponta para a função.
- Treeview (ttk.Treeview): tabelas para listar dados (produtos, vendas, pedidos).
- Combobox (ttk.Combobox): seleção entre valores.
- Listbox (tk.Listbox): lista de sugestões de busca.

Layout
- Usamos `pack` para estruturas maiores (topo, painéis) e `grid` quando necessário em formulários.
- Dica: não misturar muito `pack` e `grid` dentro do mesmo container.

Variáveis de controle
- `StringVar`/`IntVar` ligam valores Python a entradas; `trace_add('write', ...)` permite reagir a mudanças para recalcular/resumir.

Eventos e atalhos
- `bind('<F5>', handler)` ou `bind_all` para atalhos globais.
- Ex.: na Tela de Vendas, F2 foca a busca; F5 finaliza; Del remove item.

Atualizando a UI
- Após operações de banco: recarregar dados (ex.: `refresh_table()`), atualizar rótulos e totais.
- Evitar operações longas na thread da UI; se necessário, considere threads e `after()`.
