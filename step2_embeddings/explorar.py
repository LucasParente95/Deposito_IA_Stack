"""
Step 2 — Embeddings: texto virando número.
Execute com:  python3 step2_embeddings/explorar.py
"""
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

print("\n" + "="*60)
print("  PARTE 1 — O que é um vetor na prática")
print("="*60)

vetor_maca = model.encode("maçã")
print(f"\n'maçã' virou um vetor de {len(vetor_maca)} dimensões")
print(f"Primeiros 8 números: {np.round(vetor_maca[:8], 4)}")
print("(cada número é uma coordenada no espaço de significado)")


print("\n" + "="*60)
print("  PARTE 2 — Distância entre palavras")
print("="*60)

palavras = ["maçã", "fruta", "banana", "leite", "martelo", "parafuso"]
vetores = model.encode(palavras)

referencia = vetores[0]  # maçã

print(f"\nReferência: 'maçã'\n")
print(f"  {'Palavra':<12} {'Similaridade':>14}  {'Interpretação'}")
print(f"  {'-'*12} {'-'*14}  {'-'*20}")

for palavra, vetor in zip(palavras[1:], vetores[1:]):
    similaridade = np.dot(referencia, vetor) / (np.linalg.norm(referencia) * np.linalg.norm(vetor))
    pct = similaridade * 100
    if pct >= 75:
        interpretacao = "muito próximo"
    elif pct >= 50:
        interpretacao = "relacionado"
    elif pct >= 30:
        interpretacao = "distante"
    else:
        interpretacao = "sem relação"
    print(f"  {palavra:<12} {pct:>13.1f}%  {interpretacao}")


print("\n" + "="*60)
print("  PARTE 3 — O problema que você levantou")
print("="*60)

pares_suspeitos = [
    ("leite integral", "leite desnatado"),
    ("leite integral", "suco de laranja"),
    ("frango cru",     "frango assado"),
    ("frango cru",     "cimento"),
]

print()
for a, b in pares_suspeitos:
    va, vb = model.encode([a, b])
    sim = np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb))
    print(f"  '{a}'  ←→  '{b}'")
    print(f"  Similaridade: {sim*100:.1f}%\n")
