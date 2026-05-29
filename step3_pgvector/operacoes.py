"""
Step 3 — Operações de alto nível sobre o banco vetorial.

Responsabilidade: receber valores brutos do formulário,
validar via Pydantic, gerar embedding e persistir no banco.
Separa a lógica de "preparar e salvar" da lógica de armazenamento puro (banco.py).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from models.alimento import ItemAlimentar, CategoriaAlimento
from step3_pgvector.banco import inserir_alimento


def salvar_alimento(
    user_id: str,
    nome: str,
    categoria: str,
    quantidade_raw: str,
    unidade: str,
    data_validade_raw: str,
) -> dict:
    """
    Recebe valores brutos do formulário, valida com Pydantic,
    gera embedding e salva no banco.

    Retorna dict com: ok, id, item, erro
    """
    try:
        val_date = date.fromisoformat(data_validade_raw) if data_validade_raw.strip() else None
    except ValueError:
        return {"ok": False, "erro": f"Data inválida: '{data_validade_raw}' — use AAAA-MM-DD"}

    try:
        item = ItemAlimentar(
            user_id=user_id,
            nome=nome,
            categoria=categoria,
            quantidade=float(quantidade_raw) if quantidade_raw.strip() else 1.0,
            unidade=unidade,
            data_validade=val_date,
        )
    except Exception as e:
        return {"ok": False, "erro": str(e)}

    id_ = inserir_alimento(item)
    return {"ok": True, "id": id_, "item": item, "erro": ""}


def cor_similaridade(pct: float) -> str:
    """
    Retorna cor hex baseada no percentual de similaridade vetorial.
    Verde = muito próximo | Amarelo = relacionado | Vermelho = distante.
    """
    if pct >= 50:
        return "#4caf82"
    if pct >= 30:
        return "#f0c040"
    return "#e05c5c"
