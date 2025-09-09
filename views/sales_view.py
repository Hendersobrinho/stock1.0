"""
Tela de Vendas (simplificada e intuitiva):
- Topo dividido em 2 colunas: esquerda (busca e adicionar item), direita (totais e ações).
- Parte inferior: tabela da venda (itens) com atalhos práticos.
- Mantém: busca com sugestões, Qtd, Desconto%, aplicar desconto geral, remover/limpar, finalizar, exportar CSV.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from db import Database
from models.product_model import ProductModel
from models.sale_model import SaleModel, SaleItemInput
from utils.formatting import br_money, validate_percent, to_decimal, round2
from utils.exports import export_csv
import logging

logger = logging.getLogger(__name__)


class SalesFrame(ttk.Frame):
    """Frame para registro de vendas."""

    def __init__(self, parent: tk.Widget, db: Database) -> None:
        super().__init__(parent)
        self.db = db
        self.pmodel = ProductModel(db)
        self.smodel = SaleModel(db)

        # Cabeçalho
        title = ttk.Label(self, text="Registro de Vendas", font=("Segoe UI", 14, "bold"))
        title.pack(anchor=tk.W, padx=10, pady=(8, 4))

        # Topo em 2 colunas: esquerda (buscar/adicionar), direita (totais/ações)
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=8)

        # Esquerda: Busca e Adicionar Item
        left = ttk.LabelFrame(top, text="Buscar Produto e Adicionar")
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # Busca + sugestões
        search_row = ttk.Frame(left)
        search_row.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(search_row, text="SKU / Nome / Categoria (F2):").pack(side=tk.LEFT)
        self.var_search = tk.StringVar()
        self.entry_search = ttk.Entry(search_row, textvariable=self.var_search)
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.entry_search.bind("<KeyRelease>", self._update_suggestions)
        self.entry_search.bind("<FocusIn>", lambda _: self._update_suggestions())

        self.listbox = tk.Listbox(left, height=6)
        self.listbox.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.listbox.bind("<Double-Button-1>", lambda _: self._select_suggestion())
        # Mantém a lista de produtos correspondentes às linhas do listbox
        self._suggestions: list[Product] = []

        # Detalhes do produto selecionado + inputs
        details = ttk.Frame(left)
        details.pack(fill=tk.X, padx=8, pady=(0, 8))

        # Coluna 1: SKU, Nome, Estoque
        col1 = ttk.Frame(details)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.var_sku = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_stock = tk.StringVar()
        ttk.Label(col1, text="SKU:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.var_sku, state="readonly").pack(fill=tk.X, pady=2)
        ttk.Label(col1, text="Nome:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.var_name, state="readonly").pack(fill=tk.X, pady=2)
        ttk.Label(col1, text="Estoque atual:").pack(anchor=tk.W)
        ttk.Entry(col1, textvariable=self.var_stock, state="readonly").pack(fill=tk.X, pady=2)

        # Coluna 2: Preço Unitário (destaque), Qtd, Desconto, Adicionar
        col2 = ttk.Frame(details)
        col2.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 0))
        self.var_unit = tk.StringVar()
        ttk.Label(col2, text="Preço Unitário:").pack(anchor=tk.W)
        ttk.Label(col2, textvariable=self.var_unit, font=("Segoe UI", 14, "bold"), foreground="#0a6").pack(anchor=tk.W)

        row_inputs = ttk.Frame(col2)
        row_inputs.pack(anchor=tk.W, pady=(6, 0))
        ttk.Label(row_inputs, text="Qtd:").grid(row=0, column=0, padx=(0, 4))
        self.var_qty = tk.StringVar(value="1")
        ttk.Entry(row_inputs, textvariable=self.var_qty, width=8).grid(row=0, column=1)
        ttk.Label(row_inputs, text="Desc.%:").grid(row=1, column=0, padx=(0, 4), pady=(6, 0))
        self.var_disc = tk.StringVar(value="0")
        ttk.Entry(row_inputs, textvariable=self.var_disc, width=8).grid(row=1, column=1, pady=(6, 0))
        ttk.Button(col2, text="Adicionar item", command=self._add_item).pack(fill=tk.X, pady=(10, 0))

        # Tabela de vendas recentes
        self.tree = ttk.Treeview(
            self,
            columns=("sku", "name", "qty", "unit", "disc_p", "disc_v", "subtotal"),
            show="headings",
            height=14,
        )
        for col, text, w, anchor in (
            ("sku", "SKU", 110, tk.W),
            ("name", "Produto", 260, tk.W),
            ("qty", "Qtd", 60, tk.CENTER),
            ("unit", "Preço Unit.", 110, tk.E),
            ("disc_p", "Desc.%", 80, tk.E),
            ("disc_v", "Desc.R$", 110, tk.E),
            ("subtotal", "Subtotal", 120, tk.E),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(in_=self.tree, relx=1.0, rely=0, relheight=1.0, x=-1)

        # Direita: Dados do Cliente + Totais/Ações
        right = ttk.LabelFrame(top, text="Cliente e Totais")
        right.pack(side=tk.RIGHT, fill=tk.Y)
        # Cliente
        cust = ttk.Frame(right)
        cust.pack(fill=tk.X, padx=8, pady=(8, 6))
        self.var_cust_name = tk.StringVar()
        self.var_cust_email = tk.StringVar()
        self.var_cust_addr = tk.StringVar()
        ttk.Label(cust, text="Nome:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(cust, textvariable=self.var_cust_name, width=24).grid(row=0, column=1, padx=(6, 0))
        ttk.Label(cust, text="E-mail:").grid(row=1, column=0, sticky=tk.W, pady=(6,0))
        ttk.Entry(cust, textvariable=self.var_cust_email, width=24).grid(row=1, column=1, padx=(6, 0), pady=(6,0))
        ttk.Label(cust, text="Endereço:").grid(row=2, column=0, sticky=tk.W, pady=(6,0))
        ttk.Entry(cust, textvariable=self.var_cust_addr, width=24).grid(row=2, column=1, padx=(6, 0), pady=(6,0))
        self.var_tot_gross = tk.StringVar(value=br_money(0))
        self.var_tot_disc = tk.StringVar(value=br_money(0))
        self.var_tot_net = tk.StringVar(value=br_money(0))
        ttk.Label(right, text="Total Bruto:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        ttk.Label(right, textvariable=self.var_tot_gross, font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=8)
        ttk.Label(right, text="Descontos:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        ttk.Label(right, textvariable=self.var_tot_disc, font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=8)
        ttk.Label(right, text="Total Final:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        ttk.Label(right, textvariable=self.var_tot_net, font=("Segoe UI", 14, "bold"), foreground="#083").pack(anchor=tk.W, padx=8)
        ttk.Button(right, text="Aplicar desconto geral %", command=self._apply_global_discount).pack(fill=tk.X, padx=8, pady=(12, 0))
        ttk.Button(right, text="Finalizar venda (F5)", command=self._finalize).pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Button(right, text="Remover item (Del)", command=self._remove_item).pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Button(right, text="Limpar venda", command=self._clear_sale).pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Button(right, text="Exportar CSV", command=self._export_csv).pack(fill=tk.X, padx=8, pady=(6, 8))

        # Estado da venda atual
        self._cart: list[dict] = []  # {product_id, sku, name, qty, unit_price, disc_p, disc_v, subtotal}

        # Atalhos
        self.bind_all("<F2>", lambda _: self.entry_search.focus_set())
        self.bind_all("<F5>", lambda _: self._finalize())
        self.bind_all("<Delete>", lambda _: self._remove_item())

        # Inicial
        self._update_suggestions()
        self._refresh_totals()

    # ----------------------- Busca/Sugestões --------------------------
    def _update_suggestions(self, _evt=None) -> None:
        """Atualiza a lista de sugestões conforme o texto digitado.

        Mapa de eventos:
            Entry de busca (<KeyRelease>) → chama este método → atualiza Listbox

        Estratégia didática:
            (1) Ler o texto atual; (2) consultar o modelo por múltiplos campos;
            (3) ranquear por relevância (startswith > contém); (4) popular a Listbox.
        """
        q = (self.var_search.get() or "").strip()
        # Busca ampla (se vazio, lista até 50 por nome)
        candidates = self.pmodel.search(q, q, q, q) if q else self.pmodel.list_all()
        # Scoring simples: startswith tem prioridade
        def score(p: Product) -> tuple:
            s = q.lower()
            sku = p.sku.lower()
            name = p.name.lower()
            cat = (p.category or "").lower()
            grp = (p.group_code or "").lower()
            def part_sc(txt: str) -> tuple:
                if not s:
                    return (2, 9999)  # menor prioridade quando sem busca
                if txt.startswith(s):
                    return (0, len(txt))
                if s in txt:
                    return (1, txt.find(s))
                return (2, 9999)
            # combina melhor de sku/name/cat/grp
            parts = [part_sc(sku), part_sc(name), part_sc(cat), part_sc(grp)]
            best = min(parts)
            return best + (name,)

        ordered = sorted(candidates, key=score)
        # Limita tamanho
        self._suggestions = ordered[:30] if q else ordered[:50]
        # Atualiza UI
        self.listbox.delete(0, tk.END)
        if not self._suggestions:
            self.listbox.insert(tk.END, "Nenhum produto encontrado")
            return
        for p in self._suggestions:
            cat = p.category or "-"
            grp = p.group_code or "-"
            self.listbox.insert(
                tk.END,
                f"{p.sku} | {p.name} | Cat: {cat} | Grupo: {grp} | Est.: {p.stock_qty} | {br_money(p.sale_price)}",
            )

    def _select_suggestion(self) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        # Ignora seleção de mensagem vazia
        if not self._suggestions or idx >= len(self._suggestions):
            return
        p = self._suggestions[idx]
        self.var_sku.set(p.sku)
        self.var_name.set(p.name)
        self.var_stock.set(str(p.stock_qty))
        self.var_unit.set(br_money(p.sale_price))

    # ----------------------- Itens da venda ---------------------------
    def _add_item(self) -> None:
        """Adiciona o produto selecionado ao carrinho da venda.

        Fluxo:
            Clique no botão "Adicionar item" → valida Qtd/Desconto → calcula
            subtotal bruto, desconto R$ e subtotal líquido → insere na Treeview
            e recalcula os totais da venda.
        """
        sku = self.var_sku.get().strip().upper()
        if not sku:
            messagebox.showwarning("Atenção", "Selecione um produto pelas sugestões.")
            return
        prods = self.pmodel.search(sku=sku)
        if not prods:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
        p = prods[0]
        try:
            qty = int(self.var_qty.get())
        except ValueError:
            messagebox.showwarning("Quantidade inválida", "Informe uma quantidade inteira")
            return
        if qty <= 0:
            messagebox.showwarning("Quantidade inválida", "Quantidade deve ser >= 1")
            return
        if qty > p.stock_qty:
            messagebox.showerror("Estoque insuficiente", f"Estoque atual: {p.stock_qty}")
            return

        try:
            disc_p = float(validate_percent(self.var_disc.get()))
        except Exception as e:
            messagebox.showwarning("Desconto inválido", str(e))
            return

        unit = round2(p.sale_price)
        subtotal_gross = round2(unit * qty)
        disc_v = round2(subtotal_gross * (round2(disc_p) / 100))
        subtotal_net = round2(subtotal_gross - disc_v)

        self._cart.append({
            "product_id": p.id,
            "sku": p.sku,
            "name": p.name,
            "qty": qty,
            "unit": unit,
            "disc_p": round2(disc_p),
            "disc_v": disc_v,
            "subtotal": subtotal_net,
        })
        self._refresh_table()
        self._refresh_totals()
        logger.info("Item adicionado: %s x%d (desc%%=%s)", p.sku, qty, self.var_disc.get())

    def _remove_item(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self._cart):
            del self._cart[idx]
            self._refresh_table()
            self._refresh_totals()

    def _clear_sale(self) -> None:
        """Limpa carrinho e campos da venda (mesmo se já estiver vazio)."""
        # Limpa carrinho e campos (mesmo se carrinho vazio)
        if self._cart:
            if not messagebox.askyesno("Limpar", "Deseja limpar todos os itens da venda?"):
                return
            self._cart.clear()
        self._refresh_table()
        self._refresh_totals()
        self._reset_sale_form()

    def _reset_sale_form(self) -> None:
        """Restaura o formulário para o estado inicial após limpar/finalizar."""
        # Campos de busca e seleção de produto
        self.var_search.set("")
        try:
            self.listbox.delete(0, tk.END)
        except Exception:
            pass
        self.var_sku.set("")
        self.var_name.set("")
        self.var_stock.set("")
        self.var_unit.set("")
        self.var_qty.set("1")
        self.var_disc.set("0")
        # Dados de cliente
        self.var_cust_name.set("")
        self.var_cust_email.set("")
        self.var_cust_addr.set("")
        # Foco na busca
        self.entry_search.focus_set()

    def _apply_global_discount(self) -> None:
        from tkinter import simpledialog
        v = simpledialog.askstring("Desconto Geral", "Percentual (0-100):")
        if v is None:
            return
        try:
            perc = float(validate_percent(v))
        except Exception as e:
            messagebox.showwarning("Desconto inválido", str(e))
            return
        for it in self._cart:
            unit = round2(it["unit"]) 
            qty = it["qty"]
            gross = round2(unit * qty)
            disc_v = round2(gross * (round2(perc) / 100))
            net = round2(gross - disc_v)
            it["disc_p"] = round2(perc)
            it["disc_v"] = disc_v
            it["subtotal"] = net
        self._refresh_table()
        self._refresh_totals()

    def _refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for it in self._cart:
            self.tree.insert(
                "",
                tk.END,
                values=(it["sku"], it["name"], it["qty"], br_money(it["unit"]), f"{float(it['disc_p']):.2f}%", br_money(it["disc_v"]), br_money(it["subtotal"]))
            )

    def _refresh_totals(self) -> None:
        gross = sum((round2(it["unit"]) * it["qty"]) for it in self._cart)
        disc = sum((round2(it["disc_v"]) for it in self._cart))
        net = sum((round2(it["subtotal"]) for it in self._cart))
        self.var_tot_gross.set(br_money(gross))
        self.var_tot_disc.set(br_money(disc))
        self.var_tot_net.set(br_money(net))

    def _finalize(self) -> None:
        """Finaliza a venda atual.

        Efeitos colaterais importantes:
            - Grava `sales` e `sale_items` no SQLite.
            - Cria um `order` com status AGUARDANDO (estoque não baixa aqui).
            - Limpa a UI da venda e navega para a aba "Pedidos".
        """
        if not self._cart:
            messagebox.showinfo("Atenção", "Nenhum item na venda")
            return
        # Constrói itens de entrada para model
        items = []
        for it in self._cart:
            items.append(
                SaleItemInput(
                    product_id=it["product_id"],
                    sku=it["sku"],
                    name=it["name"],
                    qty=int(it["qty"]),
                    unit_price=round2(it["unit"]),
                    discount_percent=round2(it["disc_p"]),
                )
            )
        try:
            sale_id = self.smodel.create_sale(
                items,
                customer_name=self.var_cust_name.get().strip() or None,
                customer_email=self.var_cust_email.get().strip() or None,
                customer_address=self.var_cust_addr.get().strip() or None,
            )
        except Exception as e:
            messagebox.showerror("Falha ao finalizar", str(e))
            return
        messagebox.showinfo("Venda concluída", f"Venda #{sale_id} registrada com sucesso. Pedido criado e definido como AGUARDANDO.")
        logger.info("Venda #%s concluída; pedido criado.", sale_id)
        self._cart.clear()
        self._refresh_table()
        self._refresh_totals()
        self._reset_sale_form()
        # Navega para a aba de Pedidos
        try:
            app = self.winfo_toplevel()
            if hasattr(app, "notebook") and hasattr(app, "fulfillment_tab"):
                app.notebook.select(app.fulfillment_tab)
        except Exception:
            pass

    def _export_csv(self) -> None:
        from tkinter import filedialog
        if not self._cart:
            messagebox.showinfo("Atenção", "Nenhum item para exportar")
            return
        fp = filedialog.asksaveasfilename(
            title="Exportar Venda em CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile="venda.csv",
        )
        if not fp:
            return
        rows = []
        for it in self._cart:
            rows.append([
                it["sku"], it["name"], it["qty"], f"{float(round2(it['unit'])):.2f}", f"{float(round2(it['disc_p'])):.2f}", f"{float(round2(it['disc_v'])):.2f}", f"{float(round2(it['subtotal'])):.2f}"
            ])
        export_csv(fp, ("SKU", "Produto", "Qtd", "Preço Unit.", "Desc.%", "Desc.R$", "Subtotal"), rows)
        messagebox.showinfo("Exportado", f"Arquivo salvo em\n{fp}")
