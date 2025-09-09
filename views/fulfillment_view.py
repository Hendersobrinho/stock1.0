"""
Tela de Preparação e Envio de Pedidos (Grid com filtros).

Objetivo: permitir ao operador acompanhar pedidos por status, avançar fases,
cancelar e visualizar detalhes. Integra atalhos e cores por status.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from contextlib import closing
from datetime import date, timedelta

from db import Database
from models.order_model import OrderModel
from utils.formatting import br_money, fmt_datetime_br


STATUS_COLORS = {
    "AGUARDANDO": "#fff3cd",  # amarelo claro
    "PREPARADO": "#cfe2ff",   # azul claro
    "ENVIADO": "#d1e7dd",     # verde claro
    "CANCELADO": "#f8d7da",   # vermelho claro
}


class FulfillmentFrame(ttk.Frame):
    """Grid com filtros para gestão de pedidos."""

    def __init__(self, parent: tk.Widget, db: Database) -> None:
        super().__init__(parent)
        self.db = db
        self.model = OrderModel(db)

        # Cabeçalho
        ttk.Label(self, text="Preparação e Envio de Pedidos", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, padx=10, pady=(8, 4))

        # Filtros
        filters = ttk.LabelFrame(self, text="Filtros")
        filters.pack(fill=tk.X, padx=10, pady=8)
        self.var_status = tk.StringVar(value="")
        self.var_search = tk.StringVar()
        ttk.Label(filters, text="Status:").grid(row=0, column=0, padx=6, pady=6)
        ttk.Combobox(filters, textvariable=self.var_status, state="readonly", width=22,
                     values=("", "AGUARDANDO", "PREPARADO", "ENVIADO", "CANCELADO")).grid(row=0, column=1, padx=6)
        ttk.Label(filters, text="Nº/Cliente:").grid(row=0, column=2, padx=6, pady=6)
        ttk.Entry(filters, textvariable=self.var_search, width=24).grid(row=0, column=3, padx=6)
        ttk.Button(filters, text="Aplicar", command=self.refresh).grid(row=0, column=4, padx=6)
        ttk.Button(filters, text="Limpar", command=self._clear_filters).grid(row=0, column=5, padx=6)

        # Split principal: tabela esquerda, detalhes direita
        split = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Tabela
        table_frame = ttk.Frame(split)
        self.tree = ttk.Treeview(table_frame, columns=("id", "num", "cliente", "itens", "total", "status", "criado", "prep", "env"), show="headings", height=16)
        for col, text, w, anchor in (
            ("id", "ID", 50, tk.CENTER),
            ("num", "Número", 120, tk.W),
            ("cliente", "Cliente", 180, tk.W),
            ("itens", "Itens", 60, tk.CENTER),
            ("total", "Total", 110, tk.E),
            ("status", "Status", 160, tk.W),
            ("criado", "Criado", 120, tk.W),
            ("prep", "Preparado", 120, tk.W),
            ("env", "Enviado", 120, tk.W),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(in_=self.tree, relx=1.0, rely=0, relheight=1.0, x=-1)

        # Tags por status
        for st, color in STATUS_COLORS.items():
            self.tree.tag_configure(st, background=color)

        # Ações
        actions = ttk.Frame(table_frame)
        actions.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(actions, text="Avançar status (Ctrl+Enter)", command=self._advance).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Cancelar (Del)", command=self._cancel).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Atualizar", command=self.refresh).pack(side=tk.LEFT, padx=4)

        # Detalhes
        details = ttk.LabelFrame(split, text="Detalhes do Pedido")
        self.lbl_head = ttk.Label(details, text="Selecione um pedido...", font=("Segoe UI", 11, "bold"))
        self.lbl_head.pack(anchor=tk.W, padx=10, pady=(8, 2))
        self.lbl_customer = ttk.Label(details, text="", foreground="#555")
        self.lbl_customer.pack(anchor=tk.W, padx=10, pady=(0, 6))
        self.items_tree = ttk.Treeview(details, columns=("sku", "nome", "qty", "unit", "desc_p", "desc_v", "sub"), show="headings", height=10)
        for col, text, w, anchor in (
            ("sku", "SKU", 100, tk.W),
            ("nome", "Produto", 200, tk.W),
            ("qty", "Qtd", 60, tk.CENTER),
            ("unit", "Preço Unit.", 110, tk.E),
            ("desc_p", "Desc.%", 90, tk.E),
            ("desc_v", "Desc.R$", 110, tk.E),
            ("sub", "Subtotal", 120, tk.E),
        ):
            self.items_tree.heading(col, text=text)
            self.items_tree.column(col, width=w, anchor=anchor)
        self.items_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        totals = ttk.Frame(details)
        totals.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.var_total = tk.StringVar(value=br_money(0))
        ttk.Label(totals, text="Total Final:").pack(side=tk.LEFT)
        ttk.Label(totals, textvariable=self.var_total, font=("Segoe UI", 13, "bold"), foreground="#083").pack(side=tk.LEFT, padx=(6, 0))

        # Monta paned
        split.add(table_frame, weight=3)
        split.add(details, weight=2)

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.bind_all("<Control-Return>", lambda _: self._advance())
        self.bind_all("<Delete>", lambda _: self._cancel())
        self.bind_all("<F3>", lambda _: self._quick_filter("AGUARDANDO"))
        self.bind_all("<F4>", lambda _: self._quick_filter("PREPARADO"))
        self.bind_all("<F6>", lambda _: self._quick_filter("PREPARADO"))
        self.bind_all("<F7>", lambda _: self._quick_filter("ENVIADO"))

        # Inicial
        self.refresh()

    def _clear_filters(self) -> None:
        self.var_status.set("")
        self.var_search.set("")
        self.refresh()

    def _quick_filter(self, status: str) -> None:
        self.var_status.set(status)
        self.refresh()

    def refresh(self) -> None:
        # Lista pedidos conforme filtros
        for i in self.tree.get_children():
            self.tree.delete(i)
        orders = self.model.list(status=self.var_status.get() or None, search=self.var_search.get().strip() or None)
        with closing(self.db._connect()) as conn:
            for o in orders:
                # conta itens
                cur = conn.execute("SELECT COALESCE(SUM(qty),0) FROM order_items WHERE order_id = ?;", (o["id"],))
                itens = int(cur.fetchone()[0])
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        o["id"], o["order_number"], o.get("customer_name", ""), itens, br_money(o["total_net"]), o["status"],
                        fmt_datetime_br(o["created_at"]) if o.get("created_at") else "",
                        fmt_datetime_br(o["prepared_at"]) if o.get("prepared_at") else "",
                        fmt_datetime_br(o["shipped_at"]) if o.get("shipped_at") else "",
                    ),
                    tags=(o["status"],),
                )
        # Limpa detalhes
        self._show_details(None)

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            self._show_details(None)
            return
        values = self.tree.item(sel[0], "values")
        order_id = int(values[0])
        self._show_details(order_id)

    def _show_details(self, order_id: int | None) -> None:
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        if not order_id:
            self.lbl_head.configure(text="Selecione um pedido...")
            self.lbl_customer.configure(text="")
            self.var_total.set(br_money(0))
            return
        with closing(self.db._connect()) as conn:
            cur = conn.execute("SELECT * FROM orders WHERE id=?;", (order_id,))
            o = cur.fetchone()
            if not o:
                return
            self.lbl_head.configure(text=f"Pedido {o['order_number']} — {o['status']}")
            cust = (o['customer_name'] or '').strip()
            addr = (o['customer_address'] or '').strip() if 'customer_address' in o.keys() else ''
            email = (o['customer_email'] or '').strip() if 'customer_email' in o.keys() else ''
            extra = []
            if cust:
                extra.append(cust)
            if email:
                extra.append(email)
            if addr:
                extra.append(addr)
            self.lbl_customer.configure(text=" • ".join(extra))
            self.var_total.set(br_money(o["total_net"]))
            cur = conn.execute("SELECT sku, name, qty, unit_price, discount_percent, discount_value, subtotal_net FROM order_items WHERE order_id=? ORDER BY id;", (order_id,))
            for r in cur.fetchall():
                self.items_tree.insert(
                    "",
                    tk.END,
                    values=(
                        r["sku"], r["name"], r["qty"], br_money(r["unit_price"]), f"{float(r['discount_percent']):.2f}%", br_money(r["discount_value"]), br_money(r["subtotal_net"])
                    ),
                )

    def _selected_order_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return int(self.tree.item(sel[0], "values")[0])

    def _advance(self) -> None:
        oid = self._selected_order_id()
        if not oid:
            return
        # Se estiver PREPARADO, chamar ship() para baixa de estoque
        with closing(self.db._connect()) as conn:
            cur = conn.execute("SELECT status FROM orders WHERE id=?;", (oid,))
            st = cur.fetchone()[0]
        try:
            if st == "PREPARADO":
                self.model.ship(oid)
                messagebox.showinfo("Pedido enviado", f"Pedido {oid} marcado como ENVIADO e estoque baixado.")
            else:
                new_st = self.model.advance_status(oid)
                messagebox.showinfo("Status atualizado", f"Pedido {oid} avançou para {new_st}.")
        except Exception as e:
            messagebox.showerror("Falha", str(e))
            return
        self.refresh()

    def _cancel(self) -> None:
        oid = self._selected_order_id()
        if not oid:
            return
        if not messagebox.askyesno("Cancelar", "Deseja cancelar o pedido selecionado?"):
            return
        try:
            self.model.cancel(oid)
        except Exception as e:
            messagebox.showerror("Falha", str(e))
            return
        messagebox.showinfo("Cancelado", f"Pedido {oid} marcado como CANCELADO.")
        self.refresh()
