"""
Step 6 — Servidor MCP (Model Context Protocol)

O QUE É MCP:
  Protocolo da Anthropic que padroniza como modelos de IA se conectam a ferramentas.
  É para modelos de IA o que OpenAPI/Swagger é para APIs HTTP:
  um contrato de descoberta + execução que qualquer cliente entende.

COMPARAÇÃO COM OS OUTROS FORMATOS DE FERRAMENTA DESTE PROJETO:
  LangChain @tool  → funciona dentro de código Python, no processo
  FastAPI route    → funciona via HTTP, para qualquer cliente HTTP
  MCP tool         → funciona via protocolo MCP, para qualquer modelo de IA

VANTAGEM DO MCP:
  Você constrói o servidor UMA VEZ.
  Claude, Gemini, GPT ou qualquer modelo com suporte a MCP pode usar
  suas ferramentas sem nenhuma mudança no servidor.

COMO RODAR (stdio — padrão para Claude Desktop):
  python3 step6_mcp/servidor.py

COMO RODAR (HTTP SSE — para clientes remotos):
  python3 step6_mcp/servidor.py --http

COMO TESTAR COM O CLAUDE CLI:
  claude mcp add gestor-alimentos python3 step6_mcp/servidor.py
"""
import sys, os, asyncio, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from step3_pgvector.banco    import buscar_similares, listar_alimentos
from step4_rag.rag           import responder_com_rag
from step7_agente.ferramentas import alertas_vencimento as _alertas_fn

server = Server("gestor-alimentos")


# ── Definição das ferramentas ──────────────────────────────────────
# Cada @server.list_tools() expõe o catálogo para o modelo de IA descobrir.
# É como o /docs do FastAPI, mas em formato MCP.

@server.list_tools()
async def listar_ferramentas() -> list[types.Tool]:
    return [
        types.Tool(
            name="buscar_alimentos",
            description=(
                "Busca alimentos no banco usando similaridade semântica. "
                "Use para perguntas sobre tipos de alimento, ingredientes ou categorias."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "consulta": {"type": "string",  "description": "Texto da busca em linguagem natural"},
                    "user_id":  {"type": "string",  "description": "ID do usuário (isolamento multi-tenant)"},
                    "limite":   {"type": "integer", "description": "Máximo de resultados", "default": 5},
                },
                "required": ["consulta", "user_id"],
            },
        ),
        types.Tool(
            name="listar_alimentos",
            description="Lista todos os alimentos do usuário. Use para inventário completo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="alertas_vencimento",
            description=(
                "Verifica quais alimentos vencem nos próximos N dias. "
                "Use para perguntas sobre validade, o que consumir logo ou alertas de prazo."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string",  "description": "ID do usuário"},
                    "dias":    {"type": "integer", "description": "Janela em dias", "default": 7},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="perguntar_rag",
            description=(
                "Responde pergunta em linguagem natural usando RAG "
                "(busca vetorial + Gemma 3). Use para perguntas abertas que "
                "precisam de resposta elaborada ou sugestões."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pergunta": {"type": "string", "description": "Pergunta em linguagem natural"},
                    "user_id":  {"type": "string", "description": "ID do usuário"},
                },
                "required": ["pergunta", "user_id"],
            },
        ),
    ]


# ── Execução das ferramentas ───────────────────────────────────────
# @server.call_tool() recebe o nome e os argumentos escolhidos pelo modelo.
# Chama a função Python correspondente e devolve o resultado como texto.

@server.call_tool()
async def executar_ferramenta(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:

    if name == "buscar_alimentos":
        resultados = buscar_similares(
            arguments["consulta"],
            arguments["user_id"],
            limite=arguments.get("limite", 5),
        )
        linhas = [
            f"- {r['nome']} ({r['categoria']}): {r['quantidade']} {r['unidade']} "
            f"[similaridade {float(r['similaridade'])*100:.0f}%]"
            for r in resultados
        ] or ["Nenhum resultado encontrado."]
        return [types.TextContent(type="text", text="\n".join(linhas))]

    elif name == "listar_alimentos":
        itens = listar_alimentos(arguments["user_id"])
        linhas = [
            f"- {i['nome']} ({i['categoria']}): {i['quantidade']} {i['unidade']}, "
            f"val: {i['data_validade'] or '—'}"
            for i in itens
        ] or ["Nenhum item encontrado."]
        return [types.TextContent(type="text", text=f"Total: {len(itens)}\n" + "\n".join(linhas))]

    elif name == "alertas_vencimento":
        resultado = _alertas_fn.invoke({
            "user_id": arguments["user_id"],
            "dias":    arguments.get("dias", 7),
        })
        return [types.TextContent(type="text", text=str(resultado))]

    elif name == "perguntar_rag":
        resultado = responder_com_rag(arguments["pergunta"], arguments["user_id"])
        return [types.TextContent(type="text", text=resultado["resposta"])]

    else:
        return [types.TextContent(type="text", text=f"Ferramenta '{name}' não encontrada.")]


# ── Entry point ────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
