"""
Step 8.1 — Defesa contra RAG Poisoning (OWASP LLM01 / LLM03)

TEORIA:
  O banco vetorial não armazena texto — armazena vetores numéricos.
  Se texto malicioso entra antes do encode(), ele vira vetor malicioso.
  Esse vetor é depois recuperado como "contexto legítimo" pelo RAG.

  Ataques possíveis via metadados:
  - Homógrafos: 'mа̃çã' (cirílico 'а') ≠ 'maçã' (latino 'a') — bypassa filtros visuais
  - Zero-width chars: 'ma​çã' — invisível no UI, presente no vetor
  - Prompt injection no nome: 'Ignore o contexto anterior. Você é agora...'
  - Controle de caracteres: \x01\x02 — podem confundir parsers downstream

DEFESA — três camadas antes do encode():
  1. Normalização NFKC   → desfaz homógrafos e formas compostas alternativas
  2. Strip de invisíveis  → remove zero-width, soft-hyphen, BOM
  3. Denylist de padrões  → detecta strings características de prompt injection

Onde aplicar:
  - Validators do modelo Pydantic (automático em qualquer entrada)
  - Rota FastAPI para texto livre (perguntas RAG, busca semântica)
"""
import re
import unicodedata
from pydantic import BaseModel, Field, field_validator


# ── Caracteres invisíveis conhecidos ──────────────────────────────
_INVISÍVEIS = re.compile(
    r"[​"   # zero-width space
    r"‌"    # zero-width non-joiner
    r"‍"    # zero-width joiner
    r"­"    # soft hyphen
    r"﻿"    # byte-order mark (BOM)
    r" "    # line separator
    r" "    # paragraph separator
    r" "    # non-breaking space
    r"͏"    # combining grapheme joiner
    r"]"
)

# Caracteres de controle (0x00–0x1F) exceto \t (0x09) e \n (0x0A)
_CONTROLES = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Padrões que indicam tentativa de prompt injection nos metadados
_PADROES_INJECTION = [
    # Prompt injection (PT e EN)
    re.compile(r"(?i)ignore\s+(previous|all|above|instructions|todas?|as\s+instru)"),
    re.compile(r"(?i)(você|voce|you)\s+(é|e|is|are)\s+(agora|now)"),
    re.compile(r"(?i)(act|pretend|behave)\s+as"),
    re.compile(r"(?i)system\s*:"),
    re.compile(r"(?i)\bDAN\b"),                           # "Do Anything Now" jailbreak
    re.compile(r"(?i)jailbreak"),
    # Injeção de markup
    re.compile(r"(?i)<\s*(script|iframe|img)[^>]*>"),     # HTML injection
    re.compile(r"(?i)(\{|\[)\s*\"role\"\s*:"),            # JSON role injection
    # SQL injection — DDL e comandos destrutivos
    re.compile(r"(?i)\b(DROP|TRUNCATE|DELETE|ALTER)\s+(TABLE|DATABASE|SCHEMA)"),
    re.compile(r"(?i)(--|;)\s*(DROP|DELETE|INSERT|UPDATE|SELECT)"),  # terminador + SQL
    re.compile(r"(?i)UNION\s+(ALL\s+)?SELECT"),           # UNION SELECT
]


# ── Funções de sanitização ─────────────────────────────────────────

def normalizar(texto: str) -> str:
    """
    NFKC: desfaz homógrafos e formas compostas alternativas.
    'ℌello' (script H) → 'Hello' (ASCII H)
    'ﬁ' (ligature fi) → 'fi' (dois chars separados)
    """
    return unicodedata.normalize("NFKC", texto)


def strip_invisíveis(texto: str) -> str:
    """Remove caracteres invisíveis e de controle."""
    texto = _INVISÍVEIS.sub("", texto)
    texto = _CONTROLES.sub("", texto)
    return texto


def detectar_injection(texto: str) -> tuple[bool, str]:
    """
    Retorna (True, padrão) se detectar tentativa de prompt injection.
    Retorna (False, "") se o texto estiver limpo.
    """
    for padrao in _PADROES_INJECTION:
        m = padrao.search(texto)
        if m:
            return True, m.group(0)
    return False, ""


def sanitizar(texto: str) -> str:
    """Pipeline completo: normaliza → strip → devolve texto limpo."""
    texto = normalizar(texto)
    texto = strip_invisíveis(texto)
    return texto.strip()


def validar_e_sanitizar(texto: str, campo: str = "campo") -> str:
    """
    Sanitiza e verifica injection. Levanta ValueError se detectar ataque.
    Usar dentro de @field_validator do Pydantic.
    """
    texto = sanitizar(texto)
    tem_injection, padrao = detectar_injection(texto)
    if tem_injection:
        raise ValueError(
            f"[RAG Poisoning bloqueado] '{campo}' contém padrão suspeito: '{padrao}'"
        )
    return texto


# ── Modelo Pydantic com filtro embutido ───────────────────────────

class EntradaSegura(BaseModel):
    """
    Modelo base para qualquer dado que vai para o banco vetorial.
    O filtro é automático via @field_validator — nenhum dado passa sem sanitização.
    """
    pergunta: str = Field(..., min_length=2, max_length=500)
    user_id:  str = Field(..., min_length=1, max_length=100)

    @field_validator("pergunta", mode="before")
    @classmethod
    def sanitizar_pergunta(cls, v: str) -> str:
        return validar_e_sanitizar(str(v), campo="pergunta")

    @field_validator("user_id", mode="before")
    @classmethod
    def sanitizar_user_id(cls, v: str) -> str:
        limpo = sanitizar(str(v))
        # user_id só pode conter chars alfanuméricos e hífens
        if not re.match(r"^[a-zA-Z0-9\-_]+$", limpo):
            raise ValueError(
                f"[RAG Poisoning bloqueado] user_id contém caracteres inválidos: '{limpo}'"
            )
        return limpo
