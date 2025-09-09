"""
Tela de Login (Frame Tkinter).

Responsável por autenticar o usuário e acionar o callback on_success do App.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from db import Database
from utils import hash_password


class LoginFrame(ttk.Frame):
    """Frame de Login com campos de usuário e senha."""

    def __init__(self, parent: tk.Widget, db: Database, on_success) -> None:
        super().__init__(parent)
        self.db = db
        self.on_success = on_success

        # Título
        title = ttk.Label(self, text="Login", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 12))

        # Container de formulário
        form = ttk.Frame(self)
        form.pack(pady=12)

        ttk.Label(form, text="Usuário:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        ttk.Label(form, text="Senha:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=6)

        self.entry_user = ttk.Entry(form)
        self.entry_pass = ttk.Entry(form, show="*")
        self.entry_user.grid(row=0, column=1, pady=6)
        self.entry_pass.grid(row=1, column=1, pady=6)

        # Dica de acesso padrão
        hint = ttk.Label(
            self,
            text="Dica: usuário 'admin' e senha 'admin' (padrão)",
            foreground="#666",
        )
        hint.pack(pady=(4, 10))

        # Botões
        btns = ttk.Frame(self)
        btns.pack(pady=8)

        btn_login = ttk.Button(btns, text="Entrar", command=self._login)
        btn_login.grid(row=0, column=0, padx=6)

        btn_clear = ttk.Button(btns, text="Limpar", command=self._clear)
        btn_clear.grid(row=0, column=1, padx=6)

        # Bind Enter para login
        self.entry_pass.bind("<Return>", lambda _: self._login())

        # Foco inicial no usuário
        self.entry_user.focus_set()

    def _clear(self) -> None:
        """Limpa os campos do formulário."""
        self.entry_user.delete(0, tk.END)
        self.entry_pass.delete(0, tk.END)
        self.entry_user.focus_set()

    def _login(self) -> None:
        """Valida as credenciais e chama o callback de sucesso."""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username or not password:
            messagebox.showwarning("Campos obrigatórios", "Informe usuário e senha.")
            return

        password_hash = hash_password(password)
        ok = self.db.validate_user(username, password_hash)
        if not ok:
            messagebox.showerror("Falha no login", "Usuário ou senha inválidos.")
            return

        # Autenticação bem-sucedida
        self.on_success(username)

