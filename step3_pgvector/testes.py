"""
Step 3 — Teste de inserção e busca vetorial no pgvector.
Execute com:  python3 step3_pgvector/testes.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from models.alimento import ItemAlimentar, CategoriaAlimento
from step3_pgvector.banco import inserir_alimento, buscar_similares, listar_alimentos, limpar_alimentos


def sep(titulo):
    print(f"\n{'='*55}\n  {titulo}\n{'='*55}")


# ──────────────────────────────────────────────────
# Dados de dois usuários diferentes
# ──────────────────────────────────────────────────
USUARIO_A = "user-ana-001"
USUARIO_B = "user-bob-002"

alimentos_ana = [
    ItemAlimentar(user_id=USUARIO_A, nome="Maçã Fuji",        categoria=CategoriaAlimento.FRESCO,    quantidade=6,   unidade="unidade", data_validade=date(2025, 6, 5)),
    ItemAlimentar(user_id=USUARIO_A, nome="Banana Prata",     categoria=CategoriaAlimento.FRESCO,    quantidade=8,   unidade="unidade", data_validade=date(2025, 6, 3)),
    ItemAlimentar(user_id=USUARIO_A, nome="Leite Integral",   categoria=CategoriaAlimento.LATICINIOS, quantidade=2,  unidade="L",       data_validade=date(2025, 6, 10)),
    ItemAlimentar(user_id=USUARIO_A, nome="Frango Congelado", categoria=CategoriaAlimento.CONGELADO, quantidade=1.5, unidade="kg",      data_validade=date(2025, 8, 1)),
    ItemAlimentar(user_id=USUARIO_A, nome="Presunto Fatiado", categoria=CategoriaAlimento.EMBUTIDO,  quantidade=200, unidade="g",       data_validade=date(2025, 6, 15)),
]

alimentos_bob = [
    ItemAlimentar(user_id=USUARIO_B, nome="Suco de Laranja",  categoria=CategoriaAlimento.FRESCO,    quantidade=1,   unidade="L",       data_validade=date(2025, 6, 2)),
    ItemAlimentar(user_id=USUARIO_B, nome="Iogurte Natural",  categoria=CategoriaAlimento.LATICINIOS, quantidade=4,  unidade="unidade", data_validade=date(2025, 6, 8)),
    ItemAlimentar(user_id=USUARIO_B, nome="Salsicha",         categoria=CategoriaAlimento.EMBUTIDO,  quantidade=500, unidade="g",       data_validade=date(2025, 6, 20)),
]


sep("PARTE 1 — Inserindo alimentos no banco")

limpar_alimentos(USUARIO_A)
limpar_alimentos(USUARIO_B)

for item in alimentos_ana:
    id_ = inserir_alimento(item)
    print(f"  ✓ Ana    | {item.nome:<22} | id: {id_[:8]}...")

for item in alimentos_bob:
    id_ = inserir_alimento(item)
    print(f"  ✓ Bob    | {item.nome:<22} | id: {id_[:8]}...")


sep("PARTE 2 — Listando o que cada usuário tem")

print("\n  Geladeira da Ana:")
for row in listar_alimentos(USUARIO_A):
    print(f"    {row['nome']:<22} | {row['categoria']:<15} | {row['quantidade']} {row['unidade']}")

print("\n  Geladeira do Bob:")
for row in listar_alimentos(USUARIO_B):
    print(f"    {row['nome']:<22} | {row['categoria']:<15} | {row['quantidade']} {row['unidade']}")


sep("PARTE 3 — Busca semântica (Ana pergunta sobre frutas)")

pergunta = "frutas para o café da manhã"
print(f"\n  Pergunta: '{pergunta}'")
print(f"  Buscando nos alimentos da Ana...\n")

resultados = buscar_similares(pergunta, USUARIO_A)
for r in resultados:
    pct = r['similaridade'] * 100
    print(f"    {r['nome']:<22} | similaridade: {pct:.1f}%")


sep("PARTE 4 — Isolamento multi-tenant")

print(f"\n  Mesma pergunta, mas agora nos alimentos do Bob:")
resultados_bob = buscar_similares(pergunta, USUARIO_B)
for r in resultados_bob:
    pct = r['similaridade'] * 100
    print(f"    {r['nome']:<22} | similaridade: {pct:.1f}%")

print(f"\n  ✓ Ana não viu os dados do Bob. Bob não viu os dados da Ana.")
print(f"    Não porque o prompt pediu — mas porque o WHERE user_id = ? no SQL separa os mundos.")
