"""
Interface combinada: Embeddings (Step 2) + pgvector (Step 3).
Fluxo completo: texto → chunks → embedding → banco → busca semântica.
Execute com:  python3 interfaces/geladeira.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import customtkinter as ctk
from tkinter import filedialog
from datetime import date, datetime

from models.alimento import ItemAlimentar, CategoriaAlimento
from step3_pgvector.banco import inserir_alimento, buscar_similares, listar_alimentos, limpar_alimentos

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CATEGORIAS  = [c.value for c in CategoriaAlimento]
UNIDADES    = ["unidade", "kg", "g", "L", "ml", "cx"]


def cor_similaridade(pct):
    if pct >= 75: return "#4caf82", "muito próximo"
    if pct >= 50: return "#f0c040", "relacionado"
    if pct >= 30: return "#e07840", "distante"
    return "#e05c5c", "sem relação"


class GeladeiraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Geladeira — Embeddings + pgvector")
        self.geometry("1000x740")
        self.resizable(True, True)
        self._modelo = None
        self._build_layout()
        threading.Thread(target=self._carregar_modelo, daemon=True).start()

    def _carregar_modelo(self):
        from sentence_transformers import SentenceTransformer
        self.after(0, lambda: self.status.configure(
            text="⏳  Carregando modelo de embeddings...", text_color="#f0c040"
        ))
        self._modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.after(0, lambda: self.status.configure(
            text="✅  Pronto", text_color="#4caf82"
        ))

    # ──────────────────────────────────────────────────
    # LAYOUT
    # ──────────────────────────────────────────────────
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="🥦  Geladeira — texto → chunk → embedding → banco → busca",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.status = ctk.CTkLabel(
            header, text="⏳  Inicializando...",
            text_color="#f0c040", font=ctk.CTkFont(size=12)
        )
        self.status.grid(row=0, column=2, sticky="e")

        tabs = ctk.CTkTabview(self, corner_radius=10)
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        tabs.add("✍️  Adicionar Item")
        tabs.add("📄  Texto / Arquivo")
        tabs.add("📦  Minha Geladeira")
        tabs.add("🔍  Busca Semântica")

        self._build_formulario(tabs.tab("✍️  Adicionar Item"))
        self._build_texto(tabs.tab("📄  Texto / Arquivo"))
        self._build_geladeira(tabs.tab("📦  Minha Geladeira"))
        self._build_busca(tabs.tab("🔍  Busca Semântica"))

    def _user_id(self):
        return self.campo_user.get().strip() or "user-demo"

    # ──────────────────────────────────────────────────
    # USER ID — barra fixa no topo de cada aba
    # ──────────────────────────────────────────────────
    def _barra_user(self, parent, row=0):
        frame = ctk.CTkFrame(parent, fg_color="#1a1a2e", corner_radius=8)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(8, 6))
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="User ID:", width=70, anchor="w").grid(
            row=0, column=0, padx=(10, 6), pady=6
        )
        self.campo_user = ctk.CTkEntry(
            frame, placeholder_text="ex: user-ana-001",
            font=ctk.CTkFont(size=13)
        )
        self.campo_user.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=6)
        self.campo_user.insert(0, "user-ana-001")

        ctk.CTkLabel(
            frame,
            text="← mude o ID para simular outro usuário",
            text_color="gray", font=ctk.CTkFont(size=11)
        ).grid(row=0, column=2, padx=(0, 10))

    # ──────────────────────────────────────────────────
    # ABA 1 — FORMULÁRIO
    # ──────────────────────────────────────────────────
    def _build_formulario(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)

        self._barra_user(parent, row=0)

        def lbl(text, row, col, **kw):
            ctk.CTkLabel(parent, text=text, anchor="w").grid(
                row=row, column=col, sticky="w", padx=10, pady=(8, 0), **kw
            )

        lbl("Nome *", 1, 0)
        self.f_nome = ctk.CTkEntry(parent, placeholder_text="ex: Maçã Fuji")
        self.f_nome.grid(row=2, column=0, sticky="ew", padx=10)

        lbl("Categoria *", 1, 1)
        self.f_cat = ctk.CTkComboBox(parent, values=CATEGORIAS)
        self.f_cat.grid(row=2, column=1, sticky="ew", padx=10)
        self.f_cat.set(CATEGORIAS[0])

        lbl("Quantidade *", 3, 0)
        self.f_qtd = ctk.CTkEntry(parent, placeholder_text="ex: 2")
        self.f_qtd.grid(row=4, column=0, sticky="ew", padx=10)

        lbl("Unidade", 3, 1)
        self.f_und = ctk.CTkComboBox(parent, values=UNIDADES)
        self.f_und.grid(row=4, column=1, sticky="ew", padx=10)
        self.f_und.set("unidade")

        lbl("Validade  (AAAA-MM-DD)", 5, 0)
        self.f_val = ctk.CTkEntry(parent, placeholder_text="ex: 2025-06-30")
        self.f_val.grid(row=6, column=0, sticky="ew", padx=10)

        ctk.CTkButton(
            parent, text="Gerar embedding e salvar no banco",
            command=self._salvar_formulario,
            fg_color="#2d6a4f", hover_color="#1b4332", height=38
        ).grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=14)

        self.f_log = ctk.CTkTextbox(
            parent, height=180, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.f_log.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        parent.grid_rowconfigure(8, weight=1)

    def _salvar_formulario(self):
        if not self._modelo:
            return
        try:
            validade = None
            v = self.f_val.get().strip()
            if v:
                validade = date.fromisoformat(v)

            item = ItemAlimentar(
                user_id=self._user_id(),
                nome=self.f_nome.get().strip(),
                categoria=self.f_cat.get(),
                quantidade=float(self.f_qtd.get().strip() or 1),
                unidade=self.f_und.get(),
                data_validade=validade,
            )
        except Exception as e:
            self._log(self.f_log, f"❌ Pydantic rejeitou: {e}", "#e05c5c")
            return

        def run():
            vetor = self._modelo.encode(item.nome)
            self.after(0, lambda: self._log(
                self.f_log,
                f"📐 Embedding gerado: {len(vetor)} dimensões  "
                f"| min: {vetor.min():.3f}  max: {vetor.max():.3f}",
                "#f0c040"
            ))
            id_ = inserir_alimento(item)
            self.after(0, lambda: self._log(
                self.f_log,
                f"✅ Salvo no banco  |  {item.nome}  |  user: {item.user_id}  |  id: {id_[:8]}...",
                "#4caf82"
            ))

        threading.Thread(target=run, daemon=True).start()

    # ──────────────────────────────────────────────────
    # ABA 2 — TEXTO / ARQUIVO (chunking)
    # ──────────────────────────────────────────────────
    def _build_texto(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        self._barra_user(parent, row=0)

        ctk.CTkLabel(
            parent,
            text="Cole uma lista de alimentos (um por linha ou separados por vírgula).\n"
                 "Cada item vira um chunk → embedding → registro no banco.",
            anchor="w", text_color="gray", font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 4))
        toolbar.grid_columnconfigure(0, weight=1)

        self.t_entrada = ctk.CTkEntry(
            toolbar, placeholder_text="ou cole texto aqui e clique em Carregar Arquivo →",
            height=34
        )
        self.t_entrada.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            toolbar, text="📂 Arquivo", width=110, height=34,
            command=self._abrir_arquivo_texto,
            fg_color="#555", hover_color="#333"
        ).grid(row=0, column=1)

        self.t_texto = ctk.CTkTextbox(
            parent, font=ctk.CTkFont(family="monospace", size=13)
        )
        self.t_texto.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 6))
        self.t_texto.insert("0.0",
            "maçã fuji\nbanana prata\nleite integral\nfrango congelado\npresunto fatiado\n"
            "iogurte natural\nsuco de laranja\nqueijo mussarela\nmanteiga\novos"
        )

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 4))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row, text="⚡ Processar chunks → banco",
            command=self._processar_chunks,
            fg_color="#2d6a4f", hover_color="#1b4332", height=36
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            btn_row, text="Limpar texto",
            command=lambda: self.t_texto.delete("0.0", "end"),
            fg_color="#555", hover_color="#333", height=36
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.t_log = ctk.CTkTextbox(
            parent, height=150, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.t_log.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _abrir_arquivo_texto(self):
        caminho = filedialog.askopenfilename(
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not caminho:
            return
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
        self.t_texto.delete("0.0", "end")
        self.t_texto.insert("0.0", conteudo)

    def _processar_chunks(self):
        if not self._modelo:
            return

        raw = self.t_texto.get("0.0", "end")
        # Fatiamento (chunking): quebra por vírgula e por nova linha
        chunks = [
            c.strip()
            for linha in raw.splitlines()
            for c in linha.split(",")
            if c.strip()
        ]

        if not chunks:
            return

        self.t_log.delete("0.0", "end")
        self._log(self.t_log, f"🔪 {len(chunks)} chunks detectados...", "#f0c040")

        def run():
            salvos = 0
            for chunk in chunks:
                try:
                    item = ItemAlimentar(
                        user_id=self._user_id(),
                        nome=chunk,
                        categoria=CategoriaAlimento.OUTRO,
                        quantidade=1,
                    )
                    inserir_alimento(item)
                    salvos += 1
                    self.after(0, lambda c=chunk: self._log(
                        self.t_log, f"  ✓ '{c}'", "#4caf82"
                    ))
                except Exception as e:
                    self.after(0, lambda c=chunk, err=e: self._log(
                        self.t_log, f"  ✗ '{c}' → {err}", "#e05c5c"
                    ))

            self.after(0, lambda: self._log(
                self.t_log,
                f"\n✅ {salvos}/{len(chunks)} itens salvos com embedding no banco.",
                "#4caf82"
            ))

        threading.Thread(target=run, daemon=True).start()

    # ──────────────────────────────────────────────────
    # ABA 3 — MINHA GELADEIRA
    # ──────────────────────────────────────────────────
    def _build_geladeira(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        self._barra_user(parent, row=0)

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        btn_row.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            btn_row, text="🔄 Atualizar lista",
            command=self._atualizar_geladeira,
            fg_color="#1f6aa5", hover_color="#144870", height=34, width=160
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            btn_row, text="🗑️ Limpar meus dados",
            command=self._limpar_geladeira,
            fg_color="#7a1f1f", hover_color="#4a0f0f", height=34, width=160
        ).grid(row=0, column=1, padx=(8, 0))

        self.g_lista = ctk.CTkScrollableFrame(
            parent, label_text="Itens no banco (filtrados pelo seu user_id)"
        )
        self.g_lista.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.g_lista.grid_columnconfigure(0, weight=1)
        self.g_widgets = []

    def _atualizar_geladeira(self):
        for w in self.g_widgets:
            w.destroy()
        self.g_widgets.clear()

        itens = listar_alimentos(self._user_id())

        if not itens:
            lbl = ctk.CTkLabel(
                self.g_lista,
                text="Nenhum item encontrado para este user_id.",
                text_color="gray"
            )
            lbl.grid(row=0, column=0, pady=20)
            self.g_widgets.append(lbl)
            return

        headers = ["Nome", "Categoria", "Qtd", "Unidade", "Validade"]
        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.g_lista, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w"
            )
            lbl.grid(row=0, column=col, padx=8, pady=(4, 8), sticky="w")
            self.g_widgets.append(lbl)

        for i, item in enumerate(itens, 1):
            vals = [
                item["nome"],
                item["categoria"],
                str(item["quantidade"]),
                item["unidade"],
                str(item["data_validade"] or "—"),
            ]
            for col, val in enumerate(vals):
                lbl = ctk.CTkLabel(self.g_lista, text=val, anchor="w")
                lbl.grid(row=i, column=col, padx=8, pady=2, sticky="w")
                self.g_widgets.append(lbl)

    def _limpar_geladeira(self):
        n = limpar_alimentos(self._user_id())
        self._atualizar_geladeira()
        self.status.configure(
            text=f"🗑️  {n} itens removidos para {self._user_id()}",
            text_color="#e07840"
        )

    # ──────────────────────────────────────────────────
    # ABA 4 — BUSCA SEMÂNTICA
    # ──────────────────────────────────────────────────
    def _build_busca(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        self._barra_user(parent, row=0)

        ctk.CTkLabel(
            parent,
            text="Digite em linguagem natural — o banco vai encontrar o que for semanticamente mais próximo.",
            anchor="w", text_color="gray", font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 4))

        busca_row = ctk.CTkFrame(parent, fg_color="transparent")
        busca_row.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        busca_row.grid_columnconfigure(0, weight=1)

        self.b_entrada = ctk.CTkEntry(
            busca_row,
            placeholder_text="ex: proteína para o jantar / algo que vence logo / frutas",
            height=38, font=ctk.CTkFont(size=13)
        )
        self.b_entrada.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.b_entrada.bind("<Return>", lambda e: self._buscar())

        ctk.CTkButton(
            busca_row, text="Buscar", width=120, height=38,
            command=self._buscar,
            fg_color="#1f6aa5", hover_color="#144870"
        ).grid(row=0, column=1)

        self.b_resultado = ctk.CTkScrollableFrame(
            parent, label_text="Resultados (ordenados por similaridade semântica)"
        )
        self.b_resultado.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.b_resultado.grid_columnconfigure(0, weight=1)
        self.b_widgets = []

    def _buscar(self):
        if not self._modelo:
            return
        texto = self.b_entrada.get().strip()
        if not texto:
            return

        def run():
            resultados = buscar_similares(texto, self._user_id(), limite=10)
            self.after(0, lambda: self._mostrar_busca(resultados))

        threading.Thread(target=run, daemon=True).start()

    def _mostrar_busca(self, resultados):
        for w in self.b_widgets:
            w.destroy()
        self.b_widgets.clear()

        if not resultados:
            lbl = ctk.CTkLabel(
                self.b_resultado,
                text="Nenhum resultado. Adicione itens primeiro.",
                text_color="gray"
            )
            lbl.grid(row=0, column=0, pady=20)
            self.b_widgets.append(lbl)
            return

        for i, r in enumerate(resultados):
            pct = float(r["similaridade"]) * 100
            cor, desc = cor_similaridade(pct)

            card = ctk.CTkFrame(self.b_resultado, corner_radius=8)
            card.grid(row=i, column=0, sticky="ew", padx=4, pady=3)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                card, text=r["nome"], anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"), width=180
            ).grid(row=0, column=0, padx=(12, 8), pady=(8, 2), sticky="w")

            ctk.CTkLabel(
                card,
                text=f"{r['categoria']}  |  {r['quantidade']} {r['unidade']}  |  val: {r['data_validade'] or '—'}",
                anchor="w", text_color="gray", font=ctk.CTkFont(size=11)
            ).grid(row=1, column=0, padx=(12, 8), pady=(0, 8), sticky="w")

            bar_col = ctk.CTkFrame(card, fg_color="transparent")
            bar_col.grid(row=0, column=1, rowspan=2, sticky="ew", padx=(0, 12))
            bar_col.grid_columnconfigure(0, weight=1)

            bar = ctk.CTkProgressBar(bar_col, height=14, progress_color=cor)
            bar.grid(row=0, column=0, sticky="ew", pady=(8, 2))
            bar.set(max(0.0, min(1.0, float(r["similaridade"]))))

            ctk.CTkLabel(
                bar_col, text=f"{pct:.1f}%  —  {desc}",
                text_color=cor, anchor="w", font=ctk.CTkFont(size=11)
            ).grid(row=1, column=0, sticky="w", pady=(0, 8))

            self.b_widgets.append(card)

    # ──────────────────────────────────────────────────
    # UTILITÁRIO
    # ──────────────────────────────────────────────────
    def _log(self, widget, msg, cor="#ffffff"):
        widget.configure(text_color=cor)
        widget.insert("end", msg + "\n")
        widget.see("end")


if __name__ == "__main__":
    app = GeladeiraApp()
    app.mainloop()
