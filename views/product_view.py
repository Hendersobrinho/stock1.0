"""
Tela de Produtos (completa): cadastro/edição com SKU único, preços (custo/venda),
estoque e estoque mínimo; busca com filtros e listagem com indicador de mínimo.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from db import Database
from models.product_model import ProductModel, Product
from utils.exports import export_csv
from utils.formatting import br_money


class ProductFrame(ttk.Frame):
    """Frame para gerenciamento de produtos."""

    def __init__(self, parent: tk.Widget, db: Database) -> None:
        super().__init__(parent)
        self.db = db
        self.model = ProductModel(db)

        # Cabeçalho
        title = ttk.Label(self, text="Produtos", font=("Segoe UI", 14, "bold"))
        title.pack(anchor=tk.W, padx=10, pady=(8, 4))

        # Topo com duas colunas: esquerda (formulário), direita (resumo)
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=8)

        # Esquerda: formulário de cadastro/edição
        form = ttk.LabelFrame(top, text="Cadastro de Produto")
        form.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.var_sku = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_category = tk.StringVar()
        self.var_group = tk.StringVar()
        self.var_cost = tk.StringVar()
        self.var_sale = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_min = tk.StringVar()

        row1 = ttk.Frame(form); row1.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(row1, text="SKU (único):").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.var_sku, width=18).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row1, text="Nome:").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.var_name).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        row2 = ttk.Frame(form); row2.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Label(row2, text="Categoria:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.var_category, width=24).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row2, text="Grupo:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.var_group, width=18).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row2, text="Preço Custo:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.var_cost, width=12).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row2, text="Preço Venda:").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.var_sale, width=12).pack(side=tk.LEFT, padx=(6, 0))

        row3 = ttk.Frame(form); row3.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Label(row3, text="Estoque:").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.var_stock, width=10).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row3, text="Estoque Mínimo:").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.var_min, width=10).pack(side=tk.LEFT, padx=(6, 12))

        btns = ttk.Frame(form)
        btns.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(btns, text="Novo", command=self._clear_form).pack(side=tk.LEFT)
        ttk.Button(btns, text="Salvar", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Excluir", command=self._delete).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Ajustar Estoque", command=self._adjust_stock).pack(side=tk.LEFT)

        # Direita: resumo (margem/markup/alerta)
        summary = ttk.LabelFrame(top, text="Resumo")
        summary.pack(side=tk.RIGHT, fill=tk.Y)
        self.lbl_margin = ttk.Label(summary, text="Margem: R$ 0,00\nMarkup: 0,00%", font=("Segoe UI", 11))
        self.lbl_margin.pack(anchor=tk.W, padx=10, pady=(10, 4))
        self.lbl_stock_alert = ttk.Label(summary, text="", foreground="#b00")
        self.lbl_stock_alert.pack(anchor=tk.W, padx=10, pady=(4, 10))

        # Filtros de busca
        filters = ttk.LabelFrame(self, text="Buscar")
        filters.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.var_fsku = tk.StringVar()
        self.var_fname = tk.StringVar()
        self.var_fcat = tk.StringVar()
        self.var_fgroup = tk.StringVar()
        ttk.Label(filters, text="SKU:").grid(row=0, column=0, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(filters, textvariable=self.var_fsku, width=16).grid(row=0, column=1, padx=6)
        ttk.Label(filters, text="Nome:").grid(row=0, column=2, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(filters, textvariable=self.var_fname, width=28).grid(row=0, column=3, padx=6)
        ttk.Label(filters, text="Categoria:").grid(row=0, column=4, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(filters, textvariable=self.var_fcat, width=18).grid(row=0, column=5, padx=6)
        ttk.Label(filters, text="Grupo:").grid(row=0, column=6, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(filters, textvariable=self.var_fgroup, width=14).grid(row=0, column=7, padx=6)
        ttk.Button(filters, text="Filtrar", command=self.refresh_table).grid(row=0, column=8, padx=6)
        ttk.Button(filters, text="Exportar CSV", command=self._export_csv).grid(row=0, column=9, padx=6)

        # Tabela (Treeview) para listar produtos
        self.tree = ttk.Treeview(
            self,
            columns=("id", "sku", "name", "category", "group", "cost", "sale", "stock", "min"),
            show="headings",
            height=14,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("sku", text="SKU")
        self.tree.heading("name", text="Produto")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("group", text="Grupo")
        self.tree.heading("cost", text="Custo")
        self.tree.heading("sale", text="Venda")
        self.tree.heading("stock", text="Estoque")
        self.tree.heading("min", text="Min")
        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("sku", width=110)
        self.tree.column("name", width=220)
        self.tree.column("category", width=120)
        self.tree.column("group", width=100)
        self.tree.column("cost", width=100, anchor=tk.E)
        self.tree.column("sale", width=100, anchor=tk.E)
        self.tree.column("stock", width=70, anchor=tk.CENTER)
        self.tree.column("min", width=60, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbar vertical
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(in_=self.tree, relx=1.0, rely=0, relheight=1.0, x=-1)

        # Cores por tag (abaixo do mínimo)
        self.tree.tag_configure("low", background="#ffecec")

        # Bind seleção
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Estado
        self._selected_id: int | None = None

        # Carrega dados iniciais
        self.refresh_table()

        # Atualiza resumo ao alterar custo/venda/estoques
        for v in (self.var_cost, self.var_sale):
            v.trace_add("write", lambda *_: self._update_margin())
        for v in (self.var_stock, self.var_min):
            v.trace_add("write", lambda *_: self._update_stock_alert())
        self._update_stock_alert()

    # ----------------------------- Ações ------------------------------
    def _clear_form(self) -> None:
        self._selected_id = None
        for v in (self.var_sku, self.var_name, self.var_category, self.var_cost, self.var_sale, self.var_stock, self.var_min):
            v.set("")
        self._update_margin()
        self._update_stock_alert()

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        values = self.tree.item(item_id, "values")
        # values = (id, sku, name, category, group, cost, sale, stock, min)
        self._selected_id = int(values[0])
        self.var_sku.set(values[1])
        self.var_name.set(values[2])
        self.var_category.set(values[3])
        self.var_group.set(values[4])
        self.var_cost.set(str(values[5]).replace("R$ ", ""))
        self.var_sale.set(str(values[6]).replace("R$ ", ""))
        self.var_stock.set(str(values[7]))
        self.var_min.set(str(values[8]))
        self._update_margin()
        self._update_stock_alert()

    def _save(self) -> None:
        sku = self.var_sku.get()
        name = self.var_name.get()
        category = self.var_category.get()
        group = self.var_group.get()
        stock = self.var_stock.get() or "0"
        min_s = self.var_min.get() or "0"
        try:
            stock_i = int(stock)
            min_i = int(min_s)
        except ValueError:
            messagebox.showwarning("Dados inválidos", "Estoque e mínimo devem ser inteiros")
            return
        try:
            if self._selected_id is None:
                self.model.create(sku, name, category, self.var_cost.get(), self.var_sale.get(), stock_i, min_i, group)
                messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso.")
            else:
                self.model.update(self._selected_id, sku, name, category, self.var_cost.get(), self.var_sale.get(), stock_i, min_i, group)
                messagebox.showinfo("Sucesso", "Produto atualizado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")
            return

        self.refresh_table()
        self._clear_form()

    def _delete(self) -> None:
        if self._selected_id is None:
            messagebox.showinfo("Atenção", "Selecione um produto para excluir.")
            return
        if not messagebox.askyesno("Confirmação", "Deseja realmente excluir o produto?"):
            return
        try:
            self.model.delete(self._selected_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao excluir: {e}")
            return
        self.refresh_table()
        self._clear_form()

    def refresh_table(self) -> None:
        # Limpa a tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Busca produtos e popula a tabela
        produtos = self.model.search(self.var_fsku.get(), self.var_fname.get(), self.var_fcat.get(), self.var_fgroup.get())
        for p in produtos:
            tag = "low" if p.stock_qty < p.min_stock else ""
            self.tree.insert(
                "",
                tk.END,
                values=(p.id, p.sku, p.name, p.category or "", p.group_code or "", br_money(p.cost_price), br_money(p.sale_price), p.stock_qty, p.min_stock),
                tags=(tag,) if tag else (),
            )

    def _update_margin(self) -> None:
        try:
            cost = float((self.var_cost.get() or "0").replace(",", "."))
            sale = float((self.var_sale.get() or "0").replace(",", "."))
        except ValueError:
            self.lbl_margin.configure(text="Margem: - | Markup: -")
            return
        margin = max(0.0, sale - cost)
        markup = 0.0 if cost == 0 else (sale / cost - 1) * 100
        self.lbl_margin.configure(text=f"Margem: {br_money(margin)}\nMarkup: {markup:.2f}%")

    def _update_stock_alert(self) -> None:
        try:
            stock = int(self.var_stock.get() or "0")
            min_s = int(self.var_min.get() or "0")
        except ValueError:
            self.lbl_stock_alert.configure(text="")
            return
        if stock < min_s:
            self.lbl_stock_alert.configure(text=f"Atenção: abaixo do mínimo (min {min_s})")
        else:
            self.lbl_stock_alert.configure(text="")

    def _adjust_stock(self) -> None:
        if self._selected_id is None:
            messagebox.showinfo("Atenção", "Selecione um produto para ajustar o estoque.")
            return
        from tkinter import simpledialog
        delta_str = simpledialog.askstring("Ajustar Estoque", "Informe ajuste (ex.: +5 ou -3):")
        if delta_str is None:
            return
        delta_str = delta_str.strip().replace(" ", "")
        try:
            delta = int(delta_str)
        except ValueError:
            messagebox.showwarning("Valor inválido", "Informe um inteiro (ex.: +5 ou -3)")
            return
        reason = simpledialog.askstring("Motivo", "Motivo do ajuste:") or "Ajuste manual"
        try:
            self.model.adjust_stock(self._selected_id, delta, reason)
        except Exception as e:
            messagebox.showerror("Falha", str(e))
            return
        self.refresh_table()
        self._update_stock_alert()

    def _export_csv(self) -> None:
        from tkinter import filedialog
        fp = filedialog.asksaveasfilename(
            title="Exportar Produtos",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile="produtos.csv",
        )
        if not fp:
            return
        produtos = self.model.search(self.var_fsku.get(), self.var_fname.get(), self.var_fcat.get())
        rows = [
            (p.id, p.sku, p.name, p.category or "", f"{p.cost_price:.2f}", f"{p.sale_price:.2f}", p.stock_qty, p.min_stock)
            for p in produtos
        ]
        export_csv(fp, ("ID", "SKU", "Nome", "Categoria", "Custo", "Venda", "Estoque", "Min"), rows)
        messagebox.showinfo("Exportado", f"Arquivo salvo em\n{fp}")
