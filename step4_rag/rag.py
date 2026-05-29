"""
Step 4 — RAG: Retrieval-Augmented Generation

O que acontece aqui:
  1. Pergunta do usuário → embedding → busca no banco vetorial (Step 3)
  2. Resultados do banco → formatados como contexto de texto
  3. Contexto + pergunta → prompt → Gemma 3 (Ollama local) → resposta

O modelo não "sabe" o que está na geladeira.
Você literalmente entrega os dados no prompt. Isso é o RAG.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from step3_pgvector.banco import buscar_similares

MODELO = "gemma3:4b"


def buscar_contexto(pergunta: str, user_id: str, limite: int = 5) -> list[dict]:
    """Busca no banco os alimentos mais relevantes para a pergunta."""
    return buscar_similares(pergunta, user_id, limite=limite)


def formatar_contexto(itens: list[dict]) -> str:
    """Transforma a lista de alimentos em texto legível para o LLM."""
    if not itens:
        return "Nenhum alimento encontrado no banco."

    linhas = []
    for item in itens:
        validade = item["data_validade"].strftime("%d/%m/%Y") if item["data_validade"] else "sem validade"
        similaridade = f'{item["similaridade"] * 100:.0f}%'
        linha = (
            f'- {item["nome"]} ({item["categoria"]}): '
            f'{item["quantidade"]} {item["unidade"]}, '
            f'validade {validade} '
            f'[relevância {similaridade}]'
        )
        linhas.append(linha)

    return "\n".join(linhas)


def montar_prompt(pergunta: str, contexto: str) -> str:
    """Monta o prompt completo que vai para o LLM."""
    return f"""Você é um assistente de gestão de alimentos domésticos.
Responda em português, de forma direta e útil.

Alimentos disponíveis:
{contexto}

Pergunta do usuário: {pergunta}

Resposta:"""


def responder_com_rag(pergunta: str, user_id: str) -> dict:
    """
    Pipeline completo: pergunta → banco → contexto → LLM → resposta.
    Retorna dicionário com a resposta e os itens que foram usados como contexto.
    """
    itens = buscar_contexto(pergunta, user_id)
    contexto = formatar_contexto(itens)
    prompt = montar_prompt(pergunta, contexto)

    resposta = ollama.chat(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "resposta": resposta.message.content.strip(),
        "itens_usados": itens,
        "contexto_enviado": contexto,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Teste do RAG — Step 4")
    print("=" * 60)

    perguntas = [
        ("user-ana-001", "o que tenho de fruta?"),
        ("user-ana-001", "tenho alguma coisa vencendo em breve?"),
        ("user-bob-002", "o que posso usar para o café da manhã?"),
    ]

    for user_id, pergunta in perguntas:
        print(f"\nUsuário: {user_id}")
        print(f"Pergunta: {pergunta}")
        print("-" * 40)

        resultado = responder_com_rag(pergunta, user_id)

        print("Itens recuperados do banco:")
        print(resultado["contexto_enviado"])
        print("\nResposta do Gemma 3:")
        print(resultado["resposta"])
        print("=" * 60)
