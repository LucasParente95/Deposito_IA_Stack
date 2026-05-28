"""
Step 2 — Interface para explorar Embeddings visualmente.
Execute com:  python3 step2_embeddings/interface.py
"""
import threading
import customtkinter as ctk
import numpy as np

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def similaridade_coseno(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cor_e_label(pct):
    if pct >= 75:
        return "#4caf82", "muito próximo"
    elif pct >= 50:
        return "#f0c040", "relacionado"
    elif pct >= 30:
        return "#e07840", "distante"
    else:
        return "#e05c5c", "sem relação"


def cor_dimensao(valor):
    """Azul para positivo, vermelho para negativo."""
    v = max(-1.0, min(1.0, float(valor)))
    if v >= 0:
        intensidade = int(v * 220)
        return f"#{15:02x}{40 + intensidade // 4:02x}{80 + intensidade:02x}"
    else:
        intensidade = int(abs(v) * 220)
        return f"#{80 + intensidade:02x}{15:02x}{15:02x}"


class EmbeddingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Step 2 — Explorador de Embeddings")
        self.geometry("960x700")
        self.resizable(True, True)
        self.model = None
        self._build_layout()
        threading.Thread(target=self._carregar_modelo, daemon=True).start()

    def _carregar_modelo(self):
        from sentence_transformers import SentenceTransformer
        self.after(0, lambda: self.status.configure(
            text="⏳  Carregando modelo...", text_color="#f0c040"
        ))
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.after(0, lambda: self.status.configure(
            text="✅  Modelo pronto  —  384 dimensões  —  multilíngue",
            text_color="#4caf82"
        ))

    # ──────────────────────────────────────────────────
    # LAYOUT PRINCIPAL
    # ──────────────────────────────────────────────────
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Explorador de Embeddings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.status = ctk.CTkLabel(
            header, text="⏳  Inicializando...",
            text_color="#f0c040", font=ctk.CTkFont(size=12)
        )
        self.status.grid(row=0, column=2, sticky="e")

        tabs = ctk.CTkTabview(self, corner_radius=10)
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        tabs.add("🔢  Vetor Bruto")
        tabs.add("📊  Comparar")
        tabs.add("🔍  Pares Suspeitos")

        self._build_vetor(tabs.tab("🔢  Vetor Bruto"))
        self._build_comparar(tabs.tab("📊  Comparar"))
        self._build_pares(tabs.tab("🔍  Pares Suspeitos"))

    # ──────────────────────────────────────────────────
    # ABA 1 — VETOR BRUTO
    # Mostra as 384 dimensões como quadradinhos coloridos.
    # Azul = valor positivo, vermelho = negativo.
    # Passe o mouse sobre um quadrado para ver o valor exato.
    # ──────────────────────────────────────────────────
    def _build_vetor(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        topo = ctk.CTkFrame(parent, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        topo.grid_columnconfigure(0, weight=1)

        self.v_entrada = ctk.CTkEntry(
            topo, placeholder_text="Digite uma palavra ou frase e pressione Enter...",
            height=38, font=ctk.CTkFont(size=13)
        )
        self.v_entrada.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.v_entrada.bind("<Return>", lambda e: self._gerar_vetor())

        ctk.CTkButton(
            topo, text="Gerar Embedding", width=160, height=38,
            command=self._gerar_vetor,
            fg_color="#1f6aa5", hover_color="#144870"
        ).grid(row=0, column=1)

        self.v_legenda = ctk.CTkLabel(
            parent,
            text="← passe o mouse sobre um quadrado para ver o valor da dimensão  "
                 "|  azul = positivo  |  vermelho = negativo",
            text_color="gray", font=ctk.CTkFont(size=11), anchor="w"
        )
        self.v_legenda.grid(row=1, column=0, sticky="w", padx=14, pady=(2, 4))

        self.v_scroll = ctk.CTkScrollableFrame(
            parent, label_text="Dimensões (384 total — 32 por linha)"
        )
        self.v_scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.v_quadrados = []

    def _gerar_vetor(self):
        if not self.model:
            return
        texto = self.v_entrada.get().strip()
        if not texto:
            return
        self.v_legenda.configure(text="⏳ Gerando...", text_color="#f0c040")
        threading.Thread(
            target=lambda: self.after(0, lambda: self._mostrar_vetor(
                self.model.encode(texto), texto
            )) or self.model.encode(texto),
            daemon=True
        ).start()
        # versão limpa sem race condition:
        def run():
            vetor = self.model.encode(texto)
            self.after(0, lambda: self._mostrar_vetor(vetor, texto))
        threading.Thread(target=run, daemon=True).start()

    def _mostrar_vetor(self, vetor, texto):
        for w in self.v_quadrados:
            w.destroy()
        self.v_quadrados.clear()

        self.v_legenda.configure(
            text=f'"{texto}"  →  {len(vetor)} dimensões  '
                 f'|  mín: {vetor.min():.3f}  máx: {vetor.max():.3f}  '
                 f'|  passe o mouse para ver cada valor',
            text_color="white"
        )

        cols = 32
        for i, val in enumerate(vetor):
            cor = cor_dimensao(val)
            q = ctk.CTkFrame(self.v_scroll, width=20, height=20, fg_color=cor, corner_radius=2)
            q.grid(row=i // cols, column=i % cols, padx=1, pady=1)
            q.bind("<Enter>", lambda e, v=val, idx=i: self.v_legenda.configure(
                text=f"Dimensão {idx:>3}  →  {v:+.5f}",
                text_color="white"
            ))
            self.v_quadrados.append(q)

    # ──────────────────────────────────────────────────
    # ABA 2 — COMPARAR SIMILARIDADE
    # ──────────────────────────────────────────────────
    def _build_comparar(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(parent, text="Referência:", anchor="w").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 2)
        )

        topo = ctk.CTkFrame(parent, fg_color="transparent")
        topo.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        topo.grid_columnconfigure(0, weight=1)

        self.c_ref = ctk.CTkEntry(
            topo, placeholder_text="ex: maçã", height=36, font=ctk.CTkFont(size=13)
        )
        self.c_ref.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            topo, text="Comparar", width=140, height=36,
            command=self._comparar,
            fg_color="#1f6aa5", hover_color="#144870"
        ).grid(row=0, column=1)

        corpo = ctk.CTkFrame(parent, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        esq = ctk.CTkFrame(corpo, fg_color="transparent")
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        esq.grid_columnconfigure(0, weight=1)
        esq.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(esq, text="Palavras para comparar (uma por linha):", anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.c_lista = ctk.CTkTextbox(esq, font=ctk.CTkFont(family="monospace", size=13))
        self.c_lista.grid(row=1, column=0, sticky="nsew")
        self.c_lista.insert("0.0",
            "fruta\nbanana\nlaranja\nleite\nmartelo\nparafuso\nalimento\nmercado\nsupermercado\ncarro"
        )

        dir_ = ctk.CTkScrollableFrame(corpo, label_text="Resultados (ordenados por similaridade)")
        dir_.grid(row=0, column=1, sticky="nsew")
        dir_.grid_columnconfigure(0, weight=1)
        self.c_resultado_frame = dir_
        self.c_bar_widgets = []

    def _comparar(self):
        if not self.model:
            return
        ref = self.c_ref.get().strip()
        palavras = [p.strip() for p in self.c_lista.get("0.0", "end").splitlines() if p.strip()]
        if not ref or not palavras:
            return

        def run():
            vecs = self.model.encode([ref] + palavras)
            ref_vec = vecs[0]
            resultados = sorted(
                [(p, similaridade_coseno(ref_vec, v)) for p, v in zip(palavras, vecs[1:])],
                key=lambda x: x[1], reverse=True
            )
            self.after(0, lambda: self._mostrar_comparar(resultados))

        threading.Thread(target=run, daemon=True).start()

    def _mostrar_comparar(self, resultados):
        for w in self.c_bar_widgets:
            w.destroy()
        self.c_bar_widgets.clear()

        for i, (palavra, sim) in enumerate(resultados):
            pct = sim * 100
            cor, desc = cor_e_label(pct)

            row = ctk.CTkFrame(self.c_resultado_frame, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=palavra, width=110, anchor="w",
                         font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=(4, 8))

            bar = ctk.CTkProgressBar(row, height=20, progress_color=cor)
            bar.grid(row=0, column=1, sticky="ew", padx=(0, 8))
            bar.set(max(0.0, min(1.0, sim)))

            ctk.CTkLabel(
                row, text=f"{pct:.1f}%  {desc}",
                width=170, anchor="w", text_color=cor,
                font=ctk.CTkFont(size=12)
            ).grid(row=0, column=2)

            self.c_bar_widgets.append(row)

    # ──────────────────────────────────────────────────
    # ABA 3 — PARES SUSPEITOS
    # ──────────────────────────────────────────────────
    def _build_pares(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            parent,
            text="Teste pares e veja onde o modelo acerta ou surpreende.\n"
                 "Formato:  frase A  |  frase B   —  uma por linha",
            anchor="w", text_color="gray", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))

        corpo = ctk.CTkFrame(parent, fg_color="transparent")
        corpo.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_columnconfigure(1, weight=1)
        corpo.grid_rowconfigure(0, weight=1)

        esq = ctk.CTkFrame(corpo, fg_color="transparent")
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        esq.grid_columnconfigure(0, weight=1)
        esq.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(esq, text="Pares:", anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        self.p_texto = ctk.CTkTextbox(esq, font=ctk.CTkFont(family="monospace", size=12))
        self.p_texto.grid(row=1, column=0, sticky="nsew")
        self.p_texto.insert("0.0",
            "leite integral | leite desnatado\n"
            "leite integral | suco de laranja\n"
            "frango cru | frango assado\n"
            "frango cru | cimento\n"
            "banana | fruta tropical\n"
            "banana | computador\n"
            "maçã | Apple iPhone\n"
            "vencido | expirado\n"
            "data de validade | prazo de validade\n"
            "frango vencido | perigo para saúde\n"
            "geladeira | freezer\n"
            "geladeira | forno\n"
        )

        ctk.CTkButton(
            esq, text="Testar todos os pares",
            command=self._testar_pares,
            fg_color="#1f6aa5", hover_color="#144870", height=36
        ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.p_resultado = ctk.CTkScrollableFrame(corpo, label_text="Resultados")
        self.p_resultado.grid(row=0, column=1, sticky="nsew")
        self.p_resultado.grid_columnconfigure(0, weight=1)
        self.p_par_widgets = []

    def _testar_pares(self):
        if not self.model:
            return
        pares = []
        for linha in self.p_texto.get("0.0", "end").splitlines():
            if "|" in linha:
                a, b = linha.split("|", 1)
                pares.append((a.strip(), b.strip()))

        if not pares:
            return

        def run():
            resultados = []
            for a, b in pares:
                va, vb = self.model.encode([a, b])
                resultados.append((a, b, similaridade_coseno(va, vb)))
            self.after(0, lambda: self._mostrar_pares(resultados))

        threading.Thread(target=run, daemon=True).start()

    def _mostrar_pares(self, resultados):
        for w in self.p_par_widgets:
            w.destroy()
        self.p_par_widgets.clear()

        for i, (a, b, sim) in enumerate(resultados):
            pct = sim * 100
            cor, desc = cor_e_label(pct)

            card = ctk.CTkFrame(self.p_resultado, corner_radius=8)
            card.grid(row=i, column=0, sticky="ew", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card, text=f'"{a}"  ↔  "{b}"',
                anchor="w", font=ctk.CTkFont(size=12), wraplength=360
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(7, 2))

            bar_row = ctk.CTkFrame(card, fg_color="transparent")
            bar_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 7))
            bar_row.grid_columnconfigure(0, weight=1)

            bar = ctk.CTkProgressBar(bar_row, height=14, progress_color=cor)
            bar.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            bar.set(max(0.0, min(1.0, sim)))

            ctk.CTkLabel(
                bar_row, text=f"{pct:.1f}%  —  {desc}",
                text_color=cor, width=170, anchor="w",
                font=ctk.CTkFont(size=11)
            ).grid(row=0, column=1)

            self.p_par_widgets.append(card)


if __name__ == "__main__":
    app = EmbeddingApp()
    app.mainloop()
