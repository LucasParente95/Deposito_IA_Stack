"""
Step 6 — Agente com LangGraph StateGraph + LangChain @tool

O que cada biblioteca faz aqui:
  LangChain (@tool):  gera schemas JSON das ferramentas automaticamente
  LangGraph (StateGraph): define o fluxo como grafo de estados com nós e arestas
  Gemma 3 (Ollama):   raciocina em texto (não suporta tool calling nativo)

Grafo de estados:
  [START] → [node_agente] → (chamou ferramenta?)
                                  ├── sim → [node_ferramentas] → [node_agente]
                                  └── não → [END]

Por que grafo e não while loop?
  O StateGraph torna o fluxo EXPLÍCITO e auditável.
  Cada nó tem uma responsabilidade única.
  As arestas condicionais definem QUANDO ir para qual nó.
  LangGraph gerencia o estado (histórico de mensagens) entre os nós.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Annotated, TypedDict
import ollama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from step7_agente.ferramentas import FERRAMENTAS

MODELO   = "gemma3:4b"
MAX_ITER = 5

_MAPA_FERRAMENTAS = {f.name: f for f in FERRAMENTAS}


# ── Estado do grafo ────────────────────────────────────────────────
# TypedDict define o que circula entre os nós.
# add_messages é um reducer do LangGraph: acumula mensagens em vez de substituir.

class Estado(TypedDict):
    messages:  Annotated[list, add_messages]
    passos:    list          # trace para a interface
    iteracoes: int           # contador de segurança


# ── Prompt e descrição das ferramentas ────────────────────────────

def _descricao_ferramentas() -> str:
    linhas = []
    for f in FERRAMENTAS:
        desc   = (f.description or "").strip().split("\n")[0]
        schema = f.args_schema.model_json_schema() if f.args_schema else {}
        props  = list(schema.get("properties", {}).keys())
        linhas.append(f"- {f.name}({', '.join(props)}): {desc}")
    return "\n".join(linhas)


def _prompt_sistema(user_id: str) -> str:
    return f"""Você é um assistente de gestão de alimentos domésticos.
user_id do usuário: {user_id}

Ferramentas disponíveis:
{_descricao_ferramentas()}

Para usar uma ferramenta, responda EXATAMENTE assim:
Pensamento: [o que você precisa descobrir]
Ação: [nome_da_ferramenta]
Argumentos: {{"arg1": "valor1"}}

Quando tiver resposta suficiente:
Pensamento: [conclusão]
Resposta Final: [resposta completa em português]

Use sempre o user_id "{user_id}" quando necessário."""


def _parsear(texto: str) -> dict:
    r = {"pensamento": "", "acao": None, "argumentos": {}, "resposta_final": None}
    m = re.search(r"Pensamento:\s*(.+?)(?=\nAção:|\nResposta Final:|$)", texto, re.DOTALL)
    if m:
        r["pensamento"] = m.group(1).strip()
    m = re.search(r"Resposta Final:\s*(.+)", texto, re.DOTALL)
    if m:
        r["resposta_final"] = m.group(1).strip()
        return r
    m = re.search(r"Ação:\s*(\w+)", texto)
    if m:
        r["acao"] = m.group(1).strip()
    m = re.search(r"Argumentos:\s*(\{.+?\})", texto, re.DOTALL)
    if m:
        try:
            r["argumentos"] = json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return r


# ── Nós do grafo ──────────────────────────────────────────────────

def node_agente(estado: Estado) -> dict:
    """
    Nó 1: o LLM raciocina.
    Recebe o histórico de mensagens, chama o Gemma 3 e decide:
      - chamar uma ferramenta (Ação + Argumentos)
      - ou encerrar (Resposta Final)
    """
    msgs_ollama = []
    for msg in estado["messages"]:
        tipo = type(msg).__name__
        if tipo in ("SystemMessage", "system"):
            msgs_ollama.append({"role": "system",    "content": msg.content})
        elif tipo in ("HumanMessage", "human"):
            msgs_ollama.append({"role": "user",      "content": msg.content})
        elif tipo in ("AIMessage", "ai"):
            msgs_ollama.append({"role": "assistant", "content": msg.content})
        else:
            msgs_ollama.append({"role": "user",      "content": str(msg.content)})

    resposta = ollama.chat(model=MODELO, messages=msgs_ollama)
    texto    = resposta.message.content.strip()
    parsed   = _parsear(texto)

    novos_passos = list(estado.get("passos", []))
    if parsed["pensamento"]:
        novos_passos.append({"tipo": "pensamento",  "conteudo": parsed["pensamento"],
                             "no": "node_agente"})
    if parsed["resposta_final"]:
        novos_passos.append({"tipo": "resposta",    "conteudo": parsed["resposta_final"],
                             "no": "node_agente"})
    elif parsed["acao"]:
        novos_passos.append({"tipo": "decisao",
                             "conteudo": f"Ferramenta: {parsed['acao']}\nArgumentos: {json.dumps(parsed['argumentos'], ensure_ascii=False)}",
                             "no": "node_agente"})

    from langchain_core.messages import AIMessage
    return {
        "messages":  [AIMessage(content=texto)],
        "passos":    novos_passos,
        "iteracoes": estado.get("iteracoes", 0) + 1,
    }


def node_ferramentas(estado: Estado) -> dict:
    """
    Nó 2: executa a ferramenta que o agente escolheu.
    Lê a última mensagem do LLM, identifica a ferramenta e chama via LangChain.
    Resultado vira nova mensagem 'user' → volta para node_agente.
    """
    ultima = estado["messages"][-1].content
    parsed = _parsear(ultima)
    nome   = parsed.get("acao") or ""
    args   = parsed.get("argumentos") or {}

    ferramenta = _MAPA_FERRAMENTAS.get(nome)
    if ferramenta:
        try:
            resultado = str(ferramenta.invoke(args))
        except Exception as e:
            resultado = f"Erro ao executar {nome}: {e}"
    else:
        resultado = f"Ferramenta '{nome}' não encontrada."

    novos_passos = list(estado.get("passos", []))
    novos_passos.append({"tipo": "observacao", "conteudo": resultado, "no": "node_ferramentas"})

    from langchain_core.messages import HumanMessage
    return {
        "messages": [HumanMessage(content=f"Observação: {resultado}")],
        "passos":   novos_passos,
    }


# ── Aresta condicional ────────────────────────────────────────────

def decidir_proximo_no(estado: Estado) -> str:
    """
    Aresta condicional do LangGraph:
      - Se o LLM escreveu 'Resposta Final' ou atingiu MAX_ITER → END
      - Se escolheu uma ferramenta → node_ferramentas
      - Senão → END (resposta sem formato esperado)
    """
    if estado.get("iteracoes", 0) >= MAX_ITER:
        return END
    ultima = estado["messages"][-1].content
    parsed = _parsear(ultima)
    if parsed["resposta_final"]:
        return END
    if parsed["acao"]:
        return "node_ferramentas"
    return END


# ── Construção do grafo ───────────────────────────────────────────

def _construir_grafo():
    grafo = StateGraph(Estado)

    grafo.add_node("node_agente",      node_agente)
    grafo.add_node("node_ferramentas", node_ferramentas)

    grafo.add_edge(START,               "node_agente")
    grafo.add_conditional_edges("node_agente", decidir_proximo_no)
    grafo.add_edge("node_ferramentas",  "node_agente")

    return grafo.compile()


# ── API pública ───────────────────────────────────────────────────

def schemas_das_ferramentas() -> list[dict]:
    """Schemas JSON gerados pelo LangChain a partir dos @tool."""
    schemas = []
    for f in FERRAMENTAS:
        schema = f.args_schema.model_json_schema() if f.args_schema else {}
        schemas.append({
            "nome":      f.name,
            "descricao": (f.description or "").strip(),
            "schema":    schema,
        })
    return schemas


def executar(pergunta: str, user_id: str) -> dict:
    """Executa o grafo LangGraph e retorna resposta + trace completo."""
    from langchain_core.messages import SystemMessage, HumanMessage

    grafo = _construir_grafo()

    estado_inicial = {
        "messages": [
            SystemMessage(content=_prompt_sistema(user_id)),
            HumanMessage(content=pergunta),
        ],
        "passos":    [{"tipo": "pergunta", "conteudo": pergunta, "no": "START"}],
        "iteracoes": 0,
    }

    estado_final = grafo.invoke(estado_inicial)

    resposta = ""
    for passo in reversed(estado_final["passos"]):
        if passo["tipo"] == "resposta":
            resposta = passo["conteudo"]
            break

    return {"resposta": resposta, "passos": estado_final["passos"]}


if __name__ == "__main__":
    r = executar("liste meus alimentos", "user-ana-001")
    for p in r["passos"]:
        print(f"\n[{p['no']} → {p['tipo'].upper()}]\n{p['conteudo']}")
    print(f"\nRESPOSTA:\n{r['resposta']}")
