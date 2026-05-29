"""
Step 2 — Lógica de geração e visualização de embeddings.

Responsabilidade: receber texto, devolver vetor numérico e
metadados de visualização. Qualquer interface pode usar isso.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer

_modelo = None


def modelo_embedding() -> SentenceTransformer:
    """Carrega o modelo uma única vez (lazy loading)."""
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _modelo


def gerar_embedding(texto: str) -> dict:
    """
    Transforma texto em vetor numérico.
    Retorna o vetor e metadados de inspeção.
    """
    vetor = modelo_embedding().encode(texto)
    return {
        "vetor":      vetor,
        "dimensoes":  len(vetor),
        "minimo":     float(vetor.min()),
        "maximo":     float(vetor.max()),
        "texto":      texto,
    }


def calcular_similaridade(vetor_a, vetor_b) -> float:
    """
    Similaridade cosseno entre dois vetores: de -1 (opostos) a 1 (idênticos).
    É exatamente o mesmo cálculo que o pgvector usa com o operador <=>.
    """
    import numpy as np
    a, b = np.array(vetor_a), np.array(vetor_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cor_dimensao(valor: float) -> str:
    """
    Converte um valor do vetor em cor hex para visualização.
    Azul  = positivo (o modelo 'ativou' essa dimensão).
    Vermelho = negativo (o modelo 'suprimiu' essa dimensão).
    """
    v = max(-1.0, min(1.0, float(valor)))
    if v >= 0:
        t = int(v * 220)
        return f"#{15:02x}{40 + t // 4:02x}{80 + t:02x}"
    else:
        t = int(abs(v) * 220)
        return f"#{80 + t:02x}{15:02x}{15:02x}"
