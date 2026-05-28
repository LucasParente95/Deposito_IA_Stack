"""
Execute com:  python3 step1_pydantic/testes.py
Observe o que passa, o que falha, e POR QUE cada erro acontece.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.alimento import ItemAlimentar, CategoriaAlimento, FonteEntrada
from models.receita import Receita, IngredienteReceita
from pydantic import ValidationError
from datetime import date


def separador(titulo: str):
    print(f"\n{'='*55}")
    print(f"  {titulo}")
    print('='*55)


# ──────────────────────────────────────────────
# CASO 1: Formulário perfeito
# ──────────────────────────────────────────────
separador("CASO 1 — Formulário perfeito")
try:
    item = ItemAlimentar(
        user_id="user-abc-123",
        nome="maçã",
        categoria=CategoriaAlimento.FRESCO,
        quantidade=2,
        unidade="unidade",
        data_compra=date(2025, 5, 1),
        data_validade=date(2025, 5, 10),
    )
    print(f"✓ Aprovado: {item.nome} | id={item.id[:8]}... | user={item.user_id}")
except ValidationError as e:
    print(f"✗ Rejeitado:\n{e}")


# ──────────────────────────────────────────────
# CASO 2: Entrada de PDF com rastreabilidade
# ──────────────────────────────────────────────
separador("CASO 2 — Entrada via PDF")
try:
    item = ItemAlimentar(
        user_id="user-abc-123",
        nome="presunto cozido",
        categoria=CategoriaAlimento.EMBUTIDO,
        quantidade=0.3,
        unidade="kg",
        fonte=FonteEntrada.PDF,
        texto_original_pdf="Presunto cozido 300g val. 22/06/2025 — nota fiscal 4521",
    )
    print(f"✓ Aprovado: {item.nome} | fonte={item.fonte} | rastreável={bool(item.texto_original_pdf)}")
except ValidationError as e:
    print(f"✗ Rejeitado:\n{e}")


# ──────────────────────────────────────────────
# CASO 3: PDF sem texto_original — deve falhar
# ──────────────────────────────────────────────
separador("CASO 3 — PDF sem rastreabilidade (deve falhar)")
try:
    item = ItemAlimentar(
        user_id="user-abc-123",
        nome="frango",
        categoria=CategoriaAlimento.FRESCO,
        quantidade=1,
        fonte=FonteEntrada.PDF,
        # texto_original_pdf ausente propositalmente
    )
    print(f"✓ Aprovado: {item.nome}")
except ValidationError as e:
    print(f"✗ Rejeitado corretamente:\n{e.errors()[0]['msg']}")


# ──────────────────────────────────────────────
# CASO 4: Validade antes da compra — deve falhar
# ──────────────────────────────────────────────
separador("CASO 4 — Validade anterior à compra (deve falhar)")
try:
    item = ItemAlimentar(
        user_id="user-abc-123",
        nome="leite integral",
        categoria=CategoriaAlimento.LATICINIOS,
        quantidade=1,
        unidade="L",
        data_compra=date(2025, 5, 20),
        data_validade=date(2025, 5, 1),  # retroativa!
    )
    print(f"✓ Aprovado: {item.nome}")
except ValidationError as e:
    print(f"✗ Rejeitado corretamente:\n{e.errors()[0]['msg']}")


# ──────────────────────────────────────────────
# CASO 5: Lixo total — deve falhar
# ──────────────────────────────────────────────
separador("CASO 5 — Lixo total (deve falhar)")
try:
    item = ItemAlimentar(
        user_id="user-abc-123",
        nome="123",          # nome numérico
        categoria="NADA",    # categoria inexistente
        quantidade=-5,       # negativo
    )
    print(f"✓ Aprovado: {item.nome}")
except ValidationError as e:
    print(f"✗ Rejeitado corretamente — {len(e.errors())} erros encontrados:")
    for err in e.errors():
        print(f"   → [{err['loc'][0]}] {err['msg']}")


# ──────────────────────────────────────────────
# CASO 6: Receita com ingrediente duplicado — deve falhar
# ──────────────────────────────────────────────
separador("CASO 6 — Receita com ingrediente duplicado (deve falhar)")
try:
    receita = Receita(
        user_id="user-abc-123",
        nome="Vitamina de Maçã",
        ingredientes=[
            IngredienteReceita(nome="maçã", quantidade=2, unidade="unidade"),
            IngredienteReceita(nome="maçã", quantidade=1, unidade="unidade"),  # duplicada
        ]
    )
    print(f"✓ Aprovado: {receita.nome}")
except ValidationError as e:
    print(f"✗ Rejeitado corretamente:\n{e.errors()[0]['msg']}")
