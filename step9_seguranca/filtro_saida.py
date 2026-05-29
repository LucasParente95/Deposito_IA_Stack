"""
Step 8.2 — Defesa contra Saída Insegura (OWASP LLM02)

TEORIA:
  O LLM pode retornar qualquer string — inclusive:
  - Resposta vazia ou com só espaços (alucinação falhando silenciosamente)
  - Resposta com o system prompt "vazado" (leakage de contexto interno)
  - Resposta com conteúdo perigoso (código, links, dados de outro usuário)
  - JSON malformado que quebra o frontend

  A defesa é uma barreira ENTRE a resposta do LLM e o cliente.
  Se a resposta não obedecer o contrato esperado, ela é descartada
  e uma resposta segura e padronizada é devolvida no lugar.

CAMADAS DA DEFESA:
  1. Validação estrutural (Pydantic) — campos obrigatórios, tipos corretos
  2. Validação de conteúdo   — não vazia, dentro do limite de tamanho
  3. Detecção de vazamento    — padrões que indicam system prompt exposto
  4. Substituição segura      — resposta inválida → mensagem de erro controlada
"""
import re
from pydantic import BaseModel, field_validator, model_validator
from typing import Any


LIMITE_RESPOSTA_CHARS = 5_000

# Padrões que indicam o LLM expôs o system prompt ou contexto interno
_PADROES_VAZAMENTO = [
    re.compile(r"(?i)user_id\s*[:=]\s*\w"),         # user_id no output
    re.compile(r"(?i)system\s*prompt"),              # menção ao system prompt
    re.compile(r"(?i)as\s+an?\s+AI\s+language"),    # auto-revelação padrão OpenAI
    re.compile(r"(?i)I\s+cannot\s+access\s+real"),  # alucinação de limitação
    re.compile(r"(?i)(minha|meu)\s+prompt"),         # prompt em português
    re.compile(r"SELECT\s+\*\s+FROM", re.IGNORECASE),  # SQL vazado
]

_RESPOSTA_SEGURA_PADRAO = (
    "Não foi possível processar a resposta. "
    "Por favor, tente reformular sua pergunta."
)


def validar_conteudo_saida(resposta: str) -> tuple[bool, str]:
    """
    Verifica se a resposta do LLM é segura para enviar ao cliente.
    Retorna (valida, motivo_do_bloqueio).
    """
    if not resposta or not resposta.strip():
        return False, "Resposta vazia"

    if len(resposta) > LIMITE_RESPOSTA_CHARS:
        return False, f"Resposta excede {LIMITE_RESPOSTA_CHARS} caracteres"

    for padrao in _PADROES_VAZAMENTO:
        m = padrao.search(resposta)
        if m:
            return False, f"Possível vazamento detectado: '{m.group(0)}'"

    return True, ""


class RespostaRAGValidada(BaseModel):
    """
    Contrato de saída da rota /perguntar.
    Se a resposta do LLM não passar na validação, é substituída pela resposta segura.
    O cliente sempre recebe um objeto válido — nunca uma exceção inesperada.
    """
    resposta:         str
    itens_usados:     list
    contexto_enviado: str
    bloqueada:        bool = False   # True se a resposta original foi substituída
    motivo_bloqueio:  str  = ""

    @field_validator("resposta", mode="before")
    @classmethod
    def nao_vazia(cls, v: Any) -> str:
        return str(v) if v else ""

    @field_validator("itens_usados", mode="before")
    @classmethod
    def lista_valida(cls, v: Any) -> list:
        return v if isinstance(v, list) else []

    @field_validator("contexto_enviado", mode="before")
    @classmethod
    def contexto_string(cls, v: Any) -> str:
        return str(v) if v else ""

    @model_validator(mode="after")
    def verificar_e_substituir(self) -> "RespostaRAGValidada":
        valida, motivo = validar_conteudo_saida(self.resposta)
        if not valida:
            self.resposta        = _RESPOSTA_SEGURA_PADRAO
            self.bloqueada       = True
            self.motivo_bloqueio = motivo
        return self


def aplicar_filtro_saida(resultado_llm: dict) -> RespostaRAGValidada:
    """
    Ponto de entrada: recebe o dict bruto do LLM e devolve resposta validada.
    Nunca levanta exceção — sempre devolve algo seguro.
    """
    return RespostaRAGValidada(
        resposta=resultado_llm.get("resposta", ""),
        itens_usados=resultado_llm.get("itens_usados", []),
        contexto_enviado=resultado_llm.get("contexto_enviado", ""),
    )
