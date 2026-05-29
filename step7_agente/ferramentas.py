"""
Step 6 — Ferramentas do agente LangChain.

Cada função decorada com @tool é uma capacidade que o agente pode decidir usar.
O agente lê a docstring para entender o que a ferramenta faz e quando usá-la.
A docstring não é comentário — é instrução para o LLM.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from langchain_core.tools import tool

from step3_pgvector.banco    import buscar_similares, listar_alimentos
from step4_rag.rag           import responder_com_rag


@tool
def buscar_alimentos(consulta: str, user_id: str) -> str:
    """
    Busca alimentos no banco usando similaridade semântica.
    Use quando o usuário perguntar sobre um tipo específico de alimento,
    ingrediente ou categoria (ex: 'frutas', 'proteínas', 'laticínios').
    Retorna os alimentos mais relevantes com percentual de similaridade.
    """
    resultados = buscar_similares(consulta, user_id, limite=5)
    if not resultados:
        return "Nenhum alimento encontrado para essa consulta."
    linhas = []
    for r in resultados:
        pct = float(r["similaridade"]) * 100
        linhas.append(f"- {r['nome']} ({r['categoria']}): {r['quantidade']} {r['unidade']} — similaridade {pct:.0f}%")
    return "\n".join(linhas)


@tool
def listar_todos_alimentos(user_id: str) -> str:
    """
    Lista todos os alimentos do usuário no banco.
    Use quando o usuário quiser ver o inventário completo
    ou quando precisar de uma visão geral do que tem disponível.
    """
    itens = listar_alimentos(user_id)
    if not itens:
        return "Nenhum alimento encontrado no banco para este usuário."
    linhas = [f"- {i['nome']} ({i['categoria']}): {i['quantidade']} {i['unidade']}, validade: {i['data_validade'] or 'não informada'}"
              for i in itens]
    return f"Total: {len(itens)} itens\n" + "\n".join(linhas)


@tool
def alertas_vencimento(user_id: str, dias: int = 7) -> str:
    """
    Verifica quais alimentos estão vencendo nos próximos N dias.
    Use quando o usuário perguntar sobre validade, o que vai vencer,
    o que precisa consumir logo ou o que está próximo do prazo.
    Padrão: próximos 7 dias.
    """
    itens = listar_alimentos(user_id)
    hoje = date.today()
    alertas = []
    sem_data = []

    for item in itens:
        val = item["data_validade"]
        if val is None:
            sem_data.append(item["nome"])
            continue
        delta = (val - hoje).days
        if delta < 0:
            alertas.append(f"⚠️  VENCIDO há {abs(delta)} dia(s): {item['nome']} (venceu em {val})")
        elif delta <= dias:
            alertas.append(f"🔶 Vence em {delta} dia(s): {item['nome']} (validade {val})")

    if not alertas:
        return f"Nenhum alimento vencendo nos próximos {dias} dias."

    resultado = f"Alertas de vencimento (próximos {dias} dias):\n" + "\n".join(alertas)
    if sem_data:
        resultado += f"\n\nSem data cadastrada: {', '.join(sem_data)}"
    return resultado


@tool
def perguntar_com_rag(pergunta: str, user_id: str) -> str:
    """
    Responde uma pergunta em linguagem natural usando RAG —
    busca o contexto relevante no banco e passa para o LLM.
    Use quando o usuário fizer uma pergunta aberta sobre seus alimentos
    que exija uma resposta elaborada (sugestões, combinações, receitas).
    """
    resultado = responder_com_rag(pergunta, user_id)
    return resultado["resposta"]


FERRAMENTAS = [buscar_alimentos, listar_todos_alimentos, alertas_vencimento, perguntar_com_rag]
