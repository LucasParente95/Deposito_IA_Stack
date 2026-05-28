"""
Interface CustomTkinter para testar os modelos Pydantic.
Execute com:  python3 step1_pydantic/interface.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pydantic import ValidationError
from datetime import date, datetime
import json
import os

from models.alimento import ItemAlimentar, CategoriaAlimento, FonteEntrada
from models.receita import Receita, IngredienteReceita

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CATEGORIAS = [c.value for c in CategoriaAlimento]
UNIDADES = ["unidade", "kg", "g", "L", "ml", "cx"]
EXTENSOES_ACEITAS = (
    ("Documentos e imagens", "*.pdf *.txt *.docx *.doc *.png *.jpg *.jpeg"),
    ("PDF", "*.pdf"),
    ("Texto", "*.txt"),
    ("Word", "*.docx *.doc"),
    ("Imagens", "*.png *.jpg *.jpeg"),
    ("Todos", "*.*"),
)


def formatar_resultado(ok: bool, obj=None, erro: ValidationError = None) -> str:
    if ok:
        dados = json.loads(obj.model_dump_json())
        linhas = ["✅  APROVADO PELO PYDANTIC\n"]
        for k, v in dados.items():
            if v is not None:
                linhas.append(f"  {k}: {v}")
        return "\n".join(linhas)
    else:
        linhas = [f"❌  REJEITADO — {len(erro.errors())} erro(s) encontrado(s)\n"]
        for e in erro.errors():
            campo = " → ".join(str(l) for l in e["loc"])
            linhas.append(f"  [{campo}]  {e['msg']}")
        return "\n".join(linhas)


def ler_arquivo(caminho: str) -> str:
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".txt":
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(caminho)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            return "[pypdf não instalado — instale com: pip3 install pypdf --break-system-packages]"
    elif ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(caminho)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return "[python-docx não instalado — instale com: pip3 install python-docx --break-system-packages]"
    elif ext in (".png", ".jpg", ".jpeg"):
        return f"[Imagem carregada: {os.path.basename(caminho)}]\n(conteúdo visual — para extração de texto use OCR)"
    return "[Formato não suportado para leitura de texto]"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Alimentos — Teste Pydantic")
        self.geometry("860x720")
        self.resizable(True, True)
        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Título
        header = ctk.CTkLabel(
            self, text="🥦  Gestor de Alimentos — Validação Pydantic",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        header.grid(row=0, column=0, pady=(18, 6), padx=20, sticky="w")

        # Abas
        self.tabs = ctk.CTkTabview(self, corner_radius=10)
        self.tabs.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        self.tabs.add("Formulário")
        self.tabs.add("Arquivo / Texto")
        self.tabs.add("Receita")

        self._build_formulario(self.tabs.tab("Formulário"))
        self._build_arquivo(self.tabs.tab("Arquivo / Texto"))
        self._build_receita(self.tabs.tab("Receita"))

    # ──────────────────────────────────────────────────
    # ABA 1 — FORMULÁRIO
    # ──────────────────────────────────────────────────
    def _build_formulario(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)

        def lbl(text, row, col, **kw):
            ctk.CTkLabel(parent, text=text, anchor="w").grid(
                row=row, column=col, sticky="w", padx=10, pady=(8, 0), **kw
            )

        lbl("User ID *", 0, 0)
        self.f_user_id = ctk.CTkEntry(parent, placeholder_text="ex: user-abc-123")
        self.f_user_id.grid(row=1, column=0, sticky="ew", padx=10)

        lbl("Nome do alimento *", 0, 1)
        self.f_nome = ctk.CTkEntry(parent, placeholder_text="ex: Maçã Fuji")
        self.f_nome.grid(row=1, column=1, sticky="ew", padx=10)

        lbl("Categoria *", 2, 0)
        self.f_categoria = ctk.CTkComboBox(parent, values=CATEGORIAS)
        self.f_categoria.grid(row=3, column=0, sticky="ew", padx=10)
        self.f_categoria.set(CATEGORIAS[0])

        lbl("Quantidade *", 2, 1)
        self.f_quantidade = ctk.CTkEntry(parent, placeholder_text="ex: 2.5")
        self.f_quantidade.grid(row=3, column=1, sticky="ew", padx=10)

        lbl("Unidade", 4, 0)
        self.f_unidade = ctk.CTkComboBox(parent, values=UNIDADES)
        self.f_unidade.grid(row=5, column=0, sticky="ew", padx=10)
        self.f_unidade.set("unidade")

        lbl("Fonte", 4, 1)
        self.f_fonte = ctk.CTkComboBox(parent, values=["formulario", "pdf"])
        self.f_fonte.grid(row=5, column=1, sticky="ew", padx=10)
        self.f_fonte.set("formulario")

        lbl("Data de Compra  (AAAA-MM-DD)", 6, 0)
        self.f_data_compra = ctk.CTkEntry(parent, placeholder_text="ex: 2025-05-01")
        self.f_data_compra.grid(row=7, column=0, sticky="ew", padx=10)

        lbl("Data de Validade  (AAAA-MM-DD)", 6, 1)
        self.f_data_validade = ctk.CTkEntry(parent, placeholder_text="ex: 2025-06-01")
        self.f_data_validade.grid(row=7, column=1, sticky="ew", padx=10)

        lbl("Texto original PDF (obrigatório se fonte = pdf)", 8, 0, columnspan=2)
        self.f_texto_pdf = ctk.CTkEntry(parent, placeholder_text="Trecho bruto do PDF...")
        self.f_texto_pdf.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10)

        btn = ctk.CTkButton(
            parent, text="Validar com Pydantic", command=self._validar_formulario,
            fg_color="#1f6aa5", hover_color="#144870", height=38,
        )
        btn.grid(row=10, column=0, columnspan=2, pady=14, padx=10, sticky="ew")

        lbl("Resultado", 11, 0, columnspan=2)
        self.f_resultado = ctk.CTkTextbox(parent, height=180, font=ctk.CTkFont(family="monospace", size=12))
        self.f_resultado.grid(row=12, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        parent.grid_rowconfigure(12, weight=1)

    def _validar_formulario(self):
        def parse_date(s):
            s = s.strip()
            if not s:
                return None
            try:
                return date.fromisoformat(s)
            except ValueError:
                raise ValueError(f"Data inválida '{s}' — use o formato AAAA-MM-DD")

        self.f_resultado.delete("0.0", "end")
        try:
            item = ItemAlimentar(
                user_id=self.f_user_id.get().strip() or None,
                nome=self.f_nome.get().strip() or None,
                categoria=self.f_categoria.get(),
                quantidade=float(self.f_quantidade.get().strip() or 0),
                unidade=self.f_unidade.get(),
                fonte=self.f_fonte.get(),
                data_compra=parse_date(self.f_data_compra.get()),
                data_validade=parse_date(self.f_data_validade.get()),
                texto_original_pdf=self.f_texto_pdf.get().strip() or None,
            )
            self.f_resultado.insert("0.0", formatar_resultado(True, obj=item))
            self.f_resultado.configure(text_color="#4caf82")
        except ValidationError as e:
            self.f_resultado.insert("0.0", formatar_resultado(False, erro=e))
            self.f_resultado.configure(text_color="#e05c5c")
        except Exception as ex:
            self.f_resultado.insert("0.0", f"⚠️  Erro inesperado:\n{ex}")
            self.f_resultado.configure(text_color="#f0a500")

    # ──────────────────────────────────────────────────
    # ABA 2 — ARQUIVO / TEXTO LIVRE
    # ──────────────────────────────────────────────────
    def _build_arquivo(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="User ID *", anchor="w").grid(row=0, column=0, padx=(0, 8))
        self.a_user_id = ctk.CTkEntry(top, placeholder_text="ex: user-abc-123")
        self.a_user_id.grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            top, text="📂  Abrir arquivo", width=140,
            command=self._abrir_arquivo,
            fg_color="#1f6aa5", hover_color="#144870",
        ).grid(row=0, column=2, padx=(10, 0))

        self.a_arquivo_label = ctk.CTkLabel(
            parent, text="Nenhum arquivo selecionado",
            text_color="gray", anchor="w", font=ctk.CTkFont(size=11)
        )
        self.a_arquivo_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(parent, text="Texto livre (cole ou edite aqui):", anchor="w").grid(
            row=2, column=0, sticky="w", padx=14
        )
        self.a_texto = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="monospace", size=12))
        self.a_texto.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 6))

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 6))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row, text="Usar texto como ItemAlimentar (PDF)",
            command=self._validar_texto_como_pdf,
            fg_color="#2d6a4f", hover_color="#1b4332", height=36,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            btn_row, text="Limpar",
            command=lambda: self.a_texto.delete("0.0", "end"),
            fg_color="#555", hover_color="#333", height=36,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        ctk.CTkLabel(parent, text="Resultado:", anchor="w").grid(
            row=5, column=0, sticky="w", padx=14
        )
        self.a_resultado = ctk.CTkTextbox(
            parent, height=140, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.a_resultado.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _abrir_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=list(EXTENSOES_ACEITAS))
        if not caminho:
            return
        self.a_arquivo_label.configure(
            text=f"📄 {os.path.basename(caminho)}", text_color="white"
        )
        conteudo = ler_arquivo(caminho)
        self.a_texto.delete("0.0", "end")
        self.a_texto.insert("0.0", conteudo)

    def _validar_texto_como_pdf(self):
        texto = self.a_texto.get("0.0", "end").strip()
        user_id = self.a_user_id.get().strip()
        self.a_resultado.delete("0.0", "end")

        if not texto:
            self.a_resultado.insert("0.0", "⚠️  Escreva ou carregue algum texto primeiro.")
            self.a_resultado.configure(text_color="#f0a500")
            return

        try:
            item = ItemAlimentar(
                user_id=user_id or None,
                nome=texto[:60].split("\n")[0],
                categoria=CategoriaAlimento.OUTRO,
                quantidade=1,
                fonte=FonteEntrada.PDF,
                texto_original_pdf=texto[:500],
            )
            self.a_resultado.insert("0.0", formatar_resultado(True, obj=item))
            self.a_resultado.configure(text_color="#4caf82")
        except ValidationError as e:
            self.a_resultado.insert("0.0", formatar_resultado(False, erro=e))
            self.a_resultado.configure(text_color="#e05c5c")
        except Exception as ex:
            self.a_resultado.insert("0.0", f"⚠️  Erro inesperado:\n{ex}")
            self.a_resultado.configure(text_color="#f0a500")

    # ──────────────────────────────────────────────────
    # ABA 3 — RECEITA
    # ──────────────────────────────────────────────────
    def _build_receita(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(parent, text="User ID *", anchor="w").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 0)
        )
        self.r_user_id = ctk.CTkEntry(parent, placeholder_text="ex: user-abc-123")
        self.r_user_id.grid(row=1, column=0, sticky="ew", padx=10)

        ctk.CTkLabel(parent, text="Nome da Receita *", anchor="w").grid(
            row=2, column=0, sticky="w", padx=14, pady=(8, 0)
        )
        self.r_nome = ctk.CTkEntry(parent, placeholder_text="ex: Salada de Frutas")
        self.r_nome.grid(row=3, column=0, sticky="ew", padx=10)

        ctk.CTkLabel(
            parent,
            text='Ingredientes — um por linha, formato:  nome, quantidade, unidade\n'
                 'Exemplo:  maçã, 2, unidade',
            anchor="w", font=ctk.CTkFont(size=12), text_color="gray",
        ).grid(row=4, column=0, sticky="w", padx=14, pady=(8, 2))

        self.r_ingredientes = ctk.CTkTextbox(
            parent, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.r_ingredientes.grid(row=5, column=0, sticky="nsew", padx=10)
        self.r_ingredientes.insert("0.0", "maçã, 2, unidade\nbanana, 3, unidade\nleite, 200, ml")

        ctk.CTkButton(
            parent, text="Validar Receita com Pydantic",
            command=self._validar_receita,
            fg_color="#1f6aa5", hover_color="#144870", height=38,
        ).grid(row=6, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(parent, text="Resultado:", anchor="w").grid(
            row=7, column=0, sticky="w", padx=14
        )
        self.r_resultado = ctk.CTkTextbox(
            parent, height=160, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.r_resultado.grid(row=8, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _validar_receita(self):
        self.r_resultado.delete("0.0", "end")
        linhas = self.r_ingredientes.get("0.0", "end").strip().splitlines()
        ingredientes = []
        erros_parse = []

        for i, linha in enumerate(linhas, 1):
            linha = linha.strip()
            if not linha:
                continue
            partes = [p.strip() for p in linha.split(",")]
            if len(partes) != 3:
                erros_parse.append(f"Linha {i}: formato inválido → '{linha}'")
                continue
            try:
                ingredientes.append(IngredienteReceita(
                    nome=partes[0],
                    quantidade=float(partes[1]),
                    unidade=partes[2],
                ))
            except Exception as ex:
                erros_parse.append(f"Linha {i}: {ex}")

        if erros_parse:
            self.r_resultado.insert("0.0", "⚠️  Problemas no formato dos ingredientes:\n" + "\n".join(erros_parse))
            self.r_resultado.configure(text_color="#f0a500")
            return

        try:
            receita = Receita(
                user_id=self.r_user_id.get().strip() or None,
                nome=self.r_nome.get().strip() or None,
                ingredientes=ingredientes,
            )
            self.r_resultado.insert("0.0", formatar_resultado(True, obj=receita))
            self.r_resultado.configure(text_color="#4caf82")
        except ValidationError as e:
            self.r_resultado.insert("0.0", formatar_resultado(False, erro=e))
            self.r_resultado.configure(text_color="#e05c5c")
        except Exception as ex:
            self.r_resultado.insert("0.0", f"⚠️  Erro inesperado:\n{ex}")
            self.r_resultado.configure(text_color="#f0a500")


if __name__ == "__main__":
    app = App()
    app.mainloop()
