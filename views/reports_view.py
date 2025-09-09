"""
Relatórios com período intuitivo (intervalos rápidos + dd/mm/aaaa),
resumo em formato brasileiro e exportações em CSV (separador ';').
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from contextlib import closing

from db import Database
from utils.exports import export_csv
from utils.formatting import br_money, br_number, fmt_datetime_br
from datetime import date, timedelta


class ReportsFrame(ttk.Frame):
    """Frame para relatórios e exportações."""

    def __init__(self, parent: tk.Widget, db: Database) -> None:
        super().__init__(parent)
        self.db = db

        # Cabeçalho
        title = ttk.Label(self, text="Relatórios", font=("Segoe UI", 14, "bold"))
        title.pack(anchor=tk.W, padx=10, pady=(8, 4))

        # Período
        period = ttk.LabelFrame(self, text="Período")
        period.pack(fill=tk.X, padx=10, pady=8)
        self.var_range = tk.StringVar(value="Este mês")
        ttk.Label(period, text="Intervalo:").grid(row=0, column=0, padx=6, pady=6, sticky=tk.W)
        cbo = ttk.Combobox(period, textvariable=self.var_range, state="readonly", width=18,
                           values=("Hoje", "Ontem", "Últimos 7 dias", "Esta semana", "Este mês", "Mês passado", "Personalizado"))
        cbo.grid(row=0, column=1, padx=6, pady=6)
        cbo.bind("<<ComboboxSelected>>", lambda _e: self._apply_quick_range())

        self.var_start = tk.StringVar()
        self.var_end = tk.StringVar()
        ttk.Label(period, text="Início (dd/mm/aaaa):").grid(row=0, column=2, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(period, textvariable=self.var_start, width=12).grid(row=0, column=3, padx=6)
        ttk.Label(period, text="Fim (dd/mm/aaaa):").grid(row=0, column=4, padx=6, pady=6, sticky=tk.W)
        ttk.Entry(period, textvariable=self.var_end, width=12).grid(row=0, column=5, padx=6)
        ttk.Button(period, text="Aplicar", command=self.refresh).grid(row=0, column=6, padx=6)

        # Resumo
        summary_frame = ttk.LabelFrame(self, text="Resumo")
        summary_frame.pack(fill=tk.X, padx=10, pady=8)

        self.lbl_vendas = ttk.Label(summary_frame, text="Vendas: 0")
        self.lbl_bruto = ttk.Label(summary_frame, text="Bruto: R$ 0,00")
        self.lbl_desc = ttk.Label(summary_frame, text="Descontos: R$ 0,00")
        self.lbl_liq = ttk.Label(summary_frame, text="Líquido: R$ 0,00")
        self.lbl_faltando = ttk.Label(summary_frame, text="Produtos em falta: 0")

        self.lbl_vendas.grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        self.lbl_bruto.grid(row=0, column=1, sticky=tk.W, padx=6, pady=6)
        self.lbl_desc.grid(row=0, column=2, sticky=tk.W, padx=6, pady=6)
        self.lbl_liq.grid(row=0, column=3, sticky=tk.W, padx=6, pady=6)
        self.lbl_faltando.grid(row=0, column=4, sticky=tk.W, padx=6, pady=6)

        ttk.Button(summary_frame, text="Atualizar", command=self.refresh).grid(row=0, column=5, padx=6, pady=6)

        # Lista de produtos sem estoque
        export_frame = ttk.LabelFrame(self, text="Exportação (CSV)")
        export_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(export_frame, text="Exportar Vendas (resumo)", command=self._export_sales_csv).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(export_frame, text="Exportar Itens (detalhado)", command=self._export_items_csv).grid(row=0, column=1, padx=6, pady=6)
        ttk.Button(export_frame, text="Exportar Pedidos (resumo)", command=self._export_orders_csv).grid(row=0, column=2, padx=6, pady=6)

        # Lista de produtos em falta
        out_frame = ttk.LabelFrame(self, text="Produtos em falta")
        out_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.tree = ttk.Treeview(out_frame, columns=("id", "sku", "nome", "categoria", "preco", "quantidade"), show="headings")
        for col, text, w, anchor in (
            ("id", "ID", 60, tk.CENTER),
            ("sku", "SKU", 110, tk.W),
            ("nome", "Nome", 220, tk.W),
            ("categoria", "Categoria", 160, tk.W),
            ("preco", "Preço (R$)", 100, tk.E),
            ("quantidade", "Qtd", 60, tk.CENTER),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(out_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(in_=self.tree, relx=1.0, rely=0, relheight=1.0, x=-1)

        # Carrega dados iniciais
        self.refresh()

    def refresh(self) -> None:
        """Atualiza resumo por período e lista de produtos em falta."""
        start_iso, end_iso = self._parse_period()
        where = []
        params: list[str] = []
        if start_iso:
            where.append("datetime >= ?")
            params.append(start_iso)
        if end_iso:
            where.append("datetime <= ?")
            params.append(end_iso + "T23:59:59")
        sql = "SELECT COUNT(*) n, COALESCE(SUM(total_gross),0), COALESCE(SUM(total_discount),0), COALESCE(SUM(total_net),0) FROM sales"
        if where:
            sql += " WHERE " + " AND ".join(where)
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            n, bruto, desc, liq = cur.fetchone()
        self.lbl_vendas.configure(text=f"Vendas: {int(n)}")
        self.lbl_bruto.configure(text=f"Bruto: {br_money(bruto)}")
        self.lbl_desc.configure(text=f"Descontos: {br_money(desc)}")
        self.lbl_liq.configure(text=f"Líquido: {br_money(liq)}")

        # Atualiza tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        with closing(self.db._connect()) as conn:
            cur = conn.execute(
                "SELECT id, sku, name, category, sale_price, stock_qty FROM products WHERE stock_qty < min_stock ORDER BY name;"
            )
            for r in cur.fetchall():
                self.tree.insert("", tk.END, values=(r["id"], r["sku"], r["name"], r["category"], f"{r['sale_price']:.2f}", r["stock_qty"]))

    def _export_sales_csv(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(title="Exportar Vendas (resumo)", defaultextension=".csv",
                                                 filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                                                 initialfile="vendas.csv")
        if not file_path:
            return
        start_iso, end_iso = self._parse_period()
        where = []
        params: list[str] = []
        if start_iso:
            where.append("datetime >= ?")
            params.append(start_iso)
        if end_iso:
            where.append("datetime <= ?")
            params.append(end_iso + "T23:59:59")
        sql = "SELECT id, sale_number, datetime, total_gross, total_discount, total_net, items_count FROM sales"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY datetime DESC;"
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        try:
            export_csv(
                file_path,
                ("ID", "Número", "Data/Hora", "Bruto", "Descontos", "Líquido", "Itens"),
                ((r["id"], r["sale_number"], fmt_datetime_br(r["datetime"]), br_number(r["total_gross"]), br_number(r["total_discount"]), br_number(r["total_net"]), r["items_count"]) for r in rows),
            )
        except Exception as e:
            messagebox.showerror("Falha ao exportar", str(e))
            return
        messagebox.showinfo("Exportado", f"Relatório salvo em:\n{file_path}")

    def _export_orders_csv(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(title="Exportar Pedidos (resumo)", defaultextension=".csv",
                                                 filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                                                 initialfile="pedidos.csv")
        if not file_path:
            return
        start_iso, end_iso = self._parse_period()
        where = []
        params: list[str] = []
        if start_iso:
            where.append("created_at >= ?")
            params.append(start_iso)
        if end_iso:
            where.append("created_at <= ?")
            params.append(end_iso + "T23:59:59")
        sql = "SELECT id, order_number, customer_name, status, total_net, created_at, prepared_at, shipped_at FROM orders"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC;"
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        try:
            export_csv(
                file_path,
                ("ID", "Número", "Cliente", "Status", "Total", "Criado", "Preparado", "Enviado"),
                ((r["id"], r["order_number"], r["customer_name"], r["status"], br_number(r["total_net"]),
                  fmt_datetime_br(r["created_at"]) if r["created_at"] else "",
                  fmt_datetime_br(r["prepared_at"]) if r["prepared_at"] else "",
                  fmt_datetime_br(r["shipped_at"]) if r["shipped_at"] else "") for r in rows),
            )
        except Exception as e:
            messagebox.showerror("Falha ao exportar", str(e))
            return
        messagebox.showinfo("Exportado", f"Relatório salvo em:\n{file_path}")

    def _export_items_csv(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(title="Exportar Itens (detalhado)", defaultextension=".csv",
                                                 filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                                                 initialfile="venda_itens.csv")
        if not file_path:
            return
        start_iso, end_iso = self._parse_period()
        where = []
        params: list[str] = []
        if start_iso:
            where.append("s.datetime >= ?")
            params.append(start_iso)
        if end_iso:
            where.append("s.datetime <= ?")
            params.append(end_iso + "T23:59:59")
        sql = (
            "SELECT s.sale_number, s.datetime, i.sku, i.name, i.qty, i.unit_price, i.discount_percent, i.discount_value, i.subtotal_gross, i.subtotal_net "
            "FROM sale_items i JOIN sales s ON s.id = i.sale_id"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY s.datetime DESC, s.sale_number;"
        with closing(self.db._connect()) as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        try:
            export_csv(
                file_path,
                ("Número", "Data/Hora", "SKU", "Produto", "Qtd", "Preço Unit.", "Desc.%", "Desc.R$", "Subtotal Bruto", "Subtotal Líquido"),
                (
                    (
                        r["sale_number"],
                        fmt_datetime_br(r["datetime"]),
                        r["sku"],
                        r["name"],
                        r["qty"],
                        br_number(r["unit_price"]),
                        br_number(r["discount_percent"]),
                        br_number(r["discount_value"]),
                        br_number(r["subtotal_gross"]),
                        br_number(r["subtotal_net"]),
                    )
                    for r in rows
                ),
            )
        except Exception as e:
            messagebox.showerror("Falha ao exportar", str(e))
            return
        messagebox.showinfo("Exportado", f"Relatório salvo em:\n{file_path}")

    # ------------------------ Helpers de período ------------------------
    def _apply_quick_range(self) -> None:
        rng = self.var_range.get()
        today = date.today()
        if rng == "Hoje":
            start = end = today
        elif rng == "Ontem":
            d = today - timedelta(days=1)
            start = end = d
        elif rng == "Últimos 7 dias":
            start = today - timedelta(days=6)
            end = today
        elif rng == "Esta semana":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        elif rng == "Este mês":
            start = today.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        elif rng == "Mês passado":
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                start = today.replace(month=today.month - 1, day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        else:
            return
        self.var_start.set(start.strftime("%d/%m/%Y"))
        self.var_end.set(end.strftime("%d/%m/%Y"))
        self.refresh()

    def _parse_period(self) -> tuple[str | None, str | None]:
        def parse_br(d: str) -> str | None:
            d = d.strip()
            if not d:
                return None
            try:
                dd, mm, yy = d.split("/")
                return f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
            except Exception:
                return None
        start_iso = parse_br(self.var_start.get())
        end_iso = parse_br(self.var_end.get())
        return start_iso, end_iso
