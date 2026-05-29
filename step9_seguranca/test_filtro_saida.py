"""
Step 8.2 — Testes do filtro de saída (Insecure Output Handling)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from step9_seguranca.filtro_saida import (
    validar_conteudo_saida, aplicar_filtro_saida, RespostaRAGValidada
)

RESULTADO_VALIDO = {
    "resposta": "Você tem maçã e banana disponíveis.",
    "itens_usados": [{"nome": "Maçã Fuji"}],
    "contexto_enviado": "Maçã Fuji (fresco)",
}


class TestValidacaoConteudo:
    def test_resposta_valida_aprovada(self):
        valida, motivo = validar_conteudo_saida("Você tem 3 maçãs.")
        assert valida
        assert motivo == ""

    def test_resposta_vazia_bloqueada(self):
        valida, motivo = validar_conteudo_saida("")
        assert not valida
        assert "vazia" in motivo.lower()

    def test_resposta_so_espacos_bloqueada(self):
        valida, motivo = validar_conteudo_saida("   \n\t  ")
        assert not valida

    def test_resposta_muito_longa_bloqueada(self):
        valida, motivo = validar_conteudo_saida("x" * 5001)
        assert not valida
        assert "5000" in motivo or "excede" in motivo.lower()

    def test_vazamento_user_id_bloqueado(self):
        valida, motivo = validar_conteudo_saida("O user_id: user-ana-001 foi encontrado")
        assert not valida
        assert "vazamento" in motivo.lower()

    def test_vazamento_system_prompt_bloqueado(self):
        valida, motivo = validar_conteudo_saida("Meu system prompt diz que devo...")
        assert not valida

    def test_sql_vazado_bloqueado(self):
        valida, motivo = validar_conteudo_saida("SELECT * FROM alimentos WHERE user_id=1")
        assert not valida

    def test_resposta_no_limite_aceita(self):
        valida, _ = validar_conteudo_saida("a" * 5000)
        assert valida


class TestFiltroSaida:
    def test_resultado_valido_passa_intacto(self):
        resp = aplicar_filtro_saida(RESULTADO_VALIDO)
        assert resp.bloqueada is False
        assert resp.resposta == RESULTADO_VALIDO["resposta"]

    def test_resposta_vazia_substituida(self):
        resp = aplicar_filtro_saida({**RESULTADO_VALIDO, "resposta": ""})
        assert resp.bloqueada is True
        assert resp.resposta != ""
        assert resp.motivo_bloqueio != ""

    def test_resposta_com_vazamento_substituida(self):
        resp = aplicar_filtro_saida({
            **RESULTADO_VALIDO,
            "resposta": "SELECT * FROM alimentos"
        })
        assert resp.bloqueada is True

    def test_resultado_sem_itens_aceito(self):
        resp = aplicar_filtro_saida({**RESULTADO_VALIDO, "itens_usados": []})
        assert resp.itens_usados == []
        assert resp.bloqueada is False

    def test_resultado_sem_chave_nao_quebra(self):
        """Nunca deve levantar exceção — sempre devolve algo seguro."""
        resp = aplicar_filtro_saida({})
        assert resp.bloqueada is True
