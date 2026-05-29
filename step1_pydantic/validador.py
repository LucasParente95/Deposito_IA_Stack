"""
Step 1 — Lógica de validação Pydantic.

Responsabilidade: receber valores brutos (strings do formulário), tentar
construir um ItemAlimentar e devolver um resultado estruturado com o status
de cada campo — para que qualquer interface possa renderizar o log.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from pydantic import ValidationError
from models.alimento import ItemAlimentar

# Descrição das regras de cada campo — o "porquê" de cada verificação
REGRAS = {
    "user_id":       "obrigatório — chave do isolamento multi-tenant",
    "nome":          "2–100 chars, não pode ser só números",
    "categoria":     "deve ser um dos enums definidos",
    "quantidade":    "número obrigatório, deve ser > 0",
    "unidade":       "um de: kg / g / L / ml / unidade / cx",
    "data_validade": "opcional — formato AAAA-MM-DD",
    "[cruzado]":     "data_validade não pode ser anterior à data_compra",
}


def validar_item(
    user_id: str,
    nome: str,
    categoria: str,
    quantidade_raw: str,
    unidade: str,
    data_validade_raw: str,
) -> dict:
    """
    Tenta construir um ItemAlimentar a partir de valores brutos.

    Retorna um dicionário com:
      - campos: lista de dicts {campo, valor, regra, ok, motivo}
      - aprovado: bool
      - item: ItemAlimentar | None
    """
    erros = {}

    # Pré-parse: converte strings antes de chegar ao Pydantic
    try:
        qtd = float(quantidade_raw) if quantidade_raw.strip() else 0.0
    except ValueError:
        qtd = 0.0
        erros["quantidade"] = f"'{quantidade_raw}' não é um número — use ponto decimal (ex: 1.5)"

    try:
        val_date = date.fromisoformat(data_validade_raw) if data_validade_raw.strip() else None
    except ValueError:
        val_date = None
        erros["data_validade"] = f"'{data_validade_raw}' não é data válida — use AAAA-MM-DD"

    # Tenta criar o modelo Pydantic
    item = None
    try:
        item = ItemAlimentar(
            user_id=user_id,
            nome=nome or None,
            categoria=categoria,
            quantidade=qtd,
            unidade=unidade,
            data_validade=val_date,
        )
    except ValidationError as e:
        for err in e.errors():
            campo = str(err["loc"][0]) if err["loc"] else "[cruzado]"
            erros.setdefault(campo, err["msg"])

    # Monta resultado campo a campo
    entradas = [
        ("user_id",       user_id            or "(vazio)"),
        ("nome",          nome               or "(vazio)"),
        ("categoria",     categoria),
        ("quantidade",    quantidade_raw     or "(vazio)"),
        ("unidade",       unidade),
        ("data_validade", data_validade_raw  or "(vazia)"),
    ]

    campos = []
    for campo, valor in entradas:
        ok = campo not in erros
        campos.append({
            "campo":  campo,
            "valor":  valor,
            "regra":  REGRAS[campo],
            "ok":     ok,
            "motivo": erros.get(campo, ""),
        })

    # Validador cruzado (model_validator)
    tem_cross = "[cruzado]" in erros or "modelo" in erros
    motivo_cross = erros.get("[cruzado]", erros.get("modelo", ""))
    cross_ativo = bool(data_validade_raw.strip()) and "data_validade" not in erros
    if cross_ativo or tem_cross:
        campos.append({
            "campo":  "[cruzado]",
            "valor":  "—",
            "regra":  REGRAS["[cruzado]"],
            "ok":     not tem_cross,
            "motivo": motivo_cross,
        })

    return {
        "campos":   campos,
        "aprovado": len(erros) == 0,
        "item":     item,
    }
