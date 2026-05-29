"""
Step 8.3 — Testes do Rate Limiter (Denial of Wallet)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pytest
from step9_seguranca.rate_limiter import RateLimiter


class TestRateLimiter:
    def _novo(self, max_req=3, janela=60):
        return RateLimiter(max_requisicoes=max_req, janela_segundos=janela)

    def test_primeira_requisicao_permitida(self):
        rl = self._novo()
        permitido, _, _ = rl.verificar("ip-teste")
        assert permitido

    def test_dentro_do_limite_permitido(self):
        rl = self._novo(max_req=3)
        for _ in range(3):
            permitido, _, _ = rl.verificar("ip-teste")
            assert permitido

    def test_alem_do_limite_bloqueado(self):
        rl = self._novo(max_req=3)
        for _ in range(3):
            rl.verificar("ip-teste")
        permitido, _, _ = rl.verificar("ip-teste")
        assert not permitido

    def test_chaves_diferentes_sao_independentes(self):
        rl = self._novo(max_req=2)
        rl.verificar("ip-a")
        rl.verificar("ip-a")
        # ip-a esgotou, mas ip-b ainda tem limite livre
        permitido_b, _, _ = rl.verificar("ip-b")
        assert permitido_b

    def test_retry_after_retornado_quando_bloqueado(self):
        rl = self._novo(max_req=1, janela=60)
        rl.verificar("ip-teste")
        permitido, _, retry = rl.verificar("ip-teste")
        assert not permitido
        assert retry > 0

    def test_janela_curta_reseta_apos_expirar(self):
        """Com janela de 1 segundo, após esperar o limite reseta."""
        rl = self._novo(max_req=1, janela=1)
        rl.verificar("ip-teste")
        time.sleep(1.1)
        permitido, _, _ = rl.verificar("ip-teste")
        assert permitido

    def test_contagem_usadas_correta(self):
        rl = self._novo(max_req=5)
        for i in range(3):
            _, usadas, _ = rl.verificar("ip-teste")
        assert usadas == 3

    def test_status_retorna_informacoes(self):
        rl = self._novo(max_req=5)
        rl.verificar("ip-teste")
        rl.verificar("ip-teste")
        s = rl.status("ip-teste")
        assert s["usadas"] == 2
        assert s["restantes"] == 3
        assert s["limite"] == 5
