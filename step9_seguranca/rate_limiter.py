"""
Step 8.3 — Defesa contra Denial of Wallet (OWASP LLM04)

TEORIA:
  Cada chamada ao LLM custa dinheiro (tokens) ou tempo de CPU (Ollama local).
  Um bug de loop infinito no frontend, ou um atacante automatizado,
  pode disparar milhares de requisições e queimar sua cota de API.

  "Denial of Wallet" é o DoS financeiro — não derruba o servidor,
  mas esgota o crédito ou o orçamento da provedora de LLM.

DEFESA — Sliding Window Rate Limiter:
  Janela deslizante de 60 segundos por chave (IP ou user_id).
  Máximo de N requisições dentro da janela.
  Implementação sem dependências externas — só threading e datetime.

  Diferente de um rate limiter fixo ("5 req/min de 00:00 a 00:01"),
  a janela deslizante conta as últimas 60 segundos a partir de agora.
  Mais justo: não reseta o contador no virar do minuto.

COMO USAR NO FASTAPI:
  from fastapi import Depends
  from step9_seguranca.rate_limiter import RateLimiter, dependencia_rate_limit

  limitador = RateLimiter(max_requisicoes=5, janela_segundos=60)

  @app.post("/perguntar")
  def perguntar(req: PerguntaRequest, _=Depends(dependencia_rate_limit)):
      ...
"""
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, max_requisicoes: int = 5, janela_segundos: int = 60):
        self.max_requisicoes  = max_requisicoes
        self.janela_segundos  = janela_segundos
        self._registros: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def verificar(self, chave: str) -> tuple[bool, int, int]:
        """
        Verifica se a chave ainda está dentro do limite.

        Retorna: (permitido, requisicoes_usadas, segundos_ate_reset)
        """
        agora    = datetime.now()
        limite   = agora - timedelta(seconds=self.janela_segundos)

        with self._lock:
            # Descarta requisições fora da janela (sliding window)
            self._registros[chave] = [
                t for t in self._registros[chave] if t > limite
            ]

            usadas = len(self._registros[chave])

            if usadas >= self.max_requisicoes:
                # Quanto tempo até a requisição mais antiga sair da janela
                mais_antiga = self._registros[chave][0]
                segundos_reset = int(
                    (mais_antiga + timedelta(seconds=self.janela_segundos) - agora).total_seconds()
                ) + 1
                return False, usadas, segundos_reset

            self._registros[chave].append(agora)
            return True, usadas + 1, 0

    def status(self, chave: str) -> dict:
        """Retorna o estado atual do limite para uma chave (útil para debug/interface)."""
        agora  = datetime.now()
        limite = agora - timedelta(seconds=self.janela_segundos)
        with self._lock:
            registros_validos = [t for t in self._registros[chave] if t > limite]
        return {
            "chave":           chave,
            "usadas":          len(registros_validos),
            "limite":          self.max_requisicoes,
            "restantes":       max(0, self.max_requisicoes - len(registros_validos)),
            "janela_segundos": self.janela_segundos,
        }


# Instância compartilhada — uma por aplicação
_limitador_global = RateLimiter(max_requisicoes=5, janela_segundos=60)


def dependencia_rate_limit(request: Request):
    """
    FastAPI Dependency: aplica rate limit por IP do cliente.
    Injete com Depends(dependencia_rate_limit) em qualquer rota.
    """
    chave = request.client.host if request.client else "desconhecido"

    permitido, usadas, segundos_reset = _limitador_global.verificar(chave)

    if not permitido:
        raise HTTPException(
            status_code=429,
            detail={
                "erro":             "Rate limit excedido",
                "limite":           _limitador_global.max_requisicoes,
                "janela_segundos":  _limitador_global.janela_segundos,
                "retry_after":      segundos_reset,
                "mensagem":         f"Máximo {_limitador_global.max_requisicoes} requisições "
                                    f"por {_limitador_global.janela_segundos}s. "
                                    f"Tente novamente em {segundos_reset}s.",
            },
            headers={
                "Retry-After":            str(segundos_reset),
                "X-RateLimit-Limit":      str(_limitador_global.max_requisicoes),
                "X-RateLimit-Remaining":  "0",
            }
        )

    return {"usadas": usadas, "restantes": _limitador_global.max_requisicoes - usadas}
