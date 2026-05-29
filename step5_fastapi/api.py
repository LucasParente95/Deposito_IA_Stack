"""
Step 5 — API FastAPI (com defesas OWASP 8.1 / 8.2 / 8.3)

Expõe o pipeline como rotas HTTP com três camadas de segurança:
  8.1 EntradaSegura  — sanitização + detecção de RAG Poisoning na entrada
  8.2 filtro_saida   — valida e substitui resposta do LLM se inválida
  8.3 rate_limiter   — máximo 5 req/min por IP (Denial of Wallet)

Execute com:
    uvicorn step5_fastapi.api:app --reload --port 8000

Documentação interativa:  http://localhost:8000/docs
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from step1_pydantic.validador           import validar_item
from step3_pgvector.banco               import buscar_similares, listar_alimentos
from step3_pgvector.operacoes           import salvar_alimento
from step4_rag.rag                      import responder_com_rag
from step9_seguranca.filtro_entrada     import EntradaSegura
from step9_seguranca.filtro_saida       import aplicar_filtro_saida, RespostaRAGValidada
from step9_seguranca.rate_limiter       import dependencia_rate_limit

app = FastAPI(
    title="Gestor de Alimentos — API",
    description=(
        "Pipeline Pydantic + pgvector + RAG.\n\n"
        "Defesas ativas: RAG Poisoning (8.1) | Output Validation (8.2) | Rate Limit (8.3)"
    ),
    version="2.0.0",
)


# ── Modelos ────────────────────────────────────────────────────────

class PerguntaRequest(EntradaSegura):
    """Herda sanitização + detecção de injection do EntradaSegura (8.1)."""
    pass

class AlimentoRequest(BaseModel):
    user_id:       str
    nome:          str
    categoria:     str
    quantidade:    str = "1"
    unidade:       str = "unidade"
    data_validade: Optional[str] = ""

class AlimentoSalvoResponse(BaseModel):
    ok:   bool
    id:   Optional[str] = None
    erro: Optional[str] = None


# ── Rotas ──────────────────────────────────────────────────────────

@app.get("/")
def raiz():
    return {
        "status": "ok",
        "pipeline": ["pydantic", "embeddings", "pgvector", "rag"],
        "defesas":  ["RAG Poisoning (8.1)", "Output Validation (8.2)", "Rate Limit 5/min (8.3)"],
    }


@app.post("/perguntar", response_model=RespostaRAGValidada)
def perguntar(
    req: PerguntaRequest,                          # 8.1: sanitiza entrada
    _rate: dict = Depends(dependencia_rate_limit), # 8.3: máx 5 req/min
):
    """
    Pergunta → RAG → resposta validada.
    Entrada filtrada (8.1), resposta validada (8.2), rate-limited (8.3).
    """
    try:
        resultado_bruto = responder_com_rag(req.pergunta, req.user_id)
        return aplicar_filtro_saida(resultado_bruto)  # 8.2: valida saída
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alimentos", response_model=AlimentoSalvoResponse)
def adicionar_alimento(
    req: AlimentoRequest,
    _rate: dict = Depends(dependencia_rate_limit),  # 8.3
):
    resultado = salvar_alimento(
        user_id=req.user_id, nome=req.nome, categoria=req.categoria,
        quantidade_raw=req.quantidade, unidade=req.unidade,
        data_validade_raw=req.data_validade or "",
    )
    if not resultado["ok"]:
        raise HTTPException(status_code=422, detail=resultado["erro"])
    return AlimentoSalvoResponse(ok=True, id=resultado["id"])


@app.get("/alimentos/{user_id}")
def listar(user_id: str):
    itens = listar_alimentos(user_id)
    return {"user_id": user_id, "total": len(itens), "itens": [dict(i) for i in itens]}


@app.get("/buscar/{user_id}")
def buscar(user_id: str, q: str, limite: int = 5):
    resultados = buscar_similares(q, user_id, limite=limite)
    return {"user_id": user_id, "consulta": q, "resultados": [dict(r) for r in resultados]}


@app.get("/rate-limit/status")
def status_rate_limit(req_fastapi: __import__("fastapi").Request):
    """Mostra o estado atual do rate limit para o IP chamador (útil para debug)."""
    from step9_seguranca.rate_limiter import _limitador_global
    chave = req_fastapi.client.host if req_fastapi.client else "desconhecido"
    return _limitador_global.status(chave)
