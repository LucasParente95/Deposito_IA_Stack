"""
Step 7 — Testes Pydantic: perfeito / ambíguo / lixo total

Cada classe de teste documenta um comportamento esperado do sistema.
Não é só "não quebrou" — é "quebrou do jeito certo" nos casos ruins.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date
from pydantic import ValidationError
from models.alimento import ItemAlimentar, CategoriaAlimento


# ── PERFEITO ──────────────────────────────────────────────────────
# Dados ideais: todos os campos corretos, sem ambiguidade.
# Esses testes documentam o caminho feliz do sistema.

class TestDadoPerfeito:
    def test_item_completo_aprovado(self):
        item = ItemAlimentar(
            user_id="user-teste-001",
            nome="Maçã Fuji",
            categoria=CategoriaAlimento.FRESCO,
            quantidade=6,
            unidade="unidade",
            data_compra=date(2026, 5, 1),
            data_validade=date(2026, 6, 1),
        )
        assert item.nome == "Maçã Fuji"
        assert item.user_id == "user-teste-001"
        assert item.quantidade == 6.0

    def test_user_id_obrigatorio_presente(self):
        """user_id não pode faltar — é a chave do isolamento multi-tenant."""
        item = ItemAlimentar(
            user_id="qualquer-id",
            nome="Banana",
            categoria=CategoriaAlimento.FRESCO,
            quantidade=3,
        )
        assert item.user_id == "qualquer-id"

    def test_nome_capitalizado_automaticamente(self):
        """O validator .title() padroniza a capitalização."""
        item = ItemAlimentar(
            user_id="u1", nome="leite integral",
            categoria=CategoriaAlimento.LATICINIOS, quantidade=1,
        )
        assert item.nome == "Leite Integral"

    def test_validade_depois_da_compra(self):
        """Data de validade posterior à compra: aprovado."""
        item = ItemAlimentar(
            user_id="u1", nome="Queijo",
            categoria=CategoriaAlimento.LATICINIOS, quantidade=1,
            data_compra=date(2026, 1, 1),
            data_validade=date(2026, 3, 1),
        )
        assert item.data_validade > item.data_compra


# ── AMBÍGUO ───────────────────────────────────────────────────────
# Dados válidos em formato mas questionáveis em conteúdo.
# Documentam o que o sistema ACEITA mesmo sendo estranho.

class TestDadoAmbiguo:
    def test_quantidade_fracionada_aceita(self):
        """0.5 kg é válido — o sistema não tem mínimo além de > 0."""
        item = ItemAlimentar(
            user_id="u1", nome="Farinha",
            categoria=CategoriaAlimento.OUTRO, quantidade=0.001,
        )
        assert item.quantidade == 0.001

    def test_nome_muito_longo_aceito(self):
        """Nome com 99 chars passa — limite é 100."""
        nome = "A" * 99
        item = ItemAlimentar(
            user_id="u1", nome=nome,
            categoria=CategoriaAlimento.OUTRO, quantidade=1,
        )
        assert len(item.nome) == 99

    def test_validade_no_passado_aceita(self):
        """Pydantic não proíbe validade histórica — isso é decisão de negócio, não de tipo."""
        item = ItemAlimentar(
            user_id="u1", nome="Feijão",
            categoria=CategoriaAlimento.OUTRO, quantidade=1,
            data_validade=date(2020, 1, 1),
        )
        assert item.data_validade == date(2020, 1, 1)

    def test_nome_com_numeros_mistos_aceito(self):
        """'Vitamina C 500mg' tem números mas não é APENAS números — passa."""
        item = ItemAlimentar(
            user_id="u1", nome="Vitamina C 500mg",
            categoria=CategoriaAlimento.OUTRO, quantidade=1,
        )
        assert "500" in item.nome


# ── LIXO TOTAL ────────────────────────────────────────────────────
# Dados completamente inválidos.
# Documentam que o sistema rejeita com clareza — sem silêncio, sem corrupção.

class TestLixoTotal:
    def test_user_id_ausente_rejeitado(self):
        """Sem user_id o dado não entra no sistema — ponto final."""
        with pytest.raises(ValidationError) as exc:
            ItemAlimentar(
                nome="Maçã", categoria=CategoriaAlimento.FRESCO, quantidade=1,
            )
        erros = [e["loc"][0] for e in exc.value.errors()]
        assert "user_id" in erros

    def test_quantidade_negativa_rejeitada(self):
        """-5 não é quantidade válida. gt=0 impede."""
        with pytest.raises(ValidationError) as exc:
            ItemAlimentar(
                user_id="u1", nome="Maçã",
                categoria=CategoriaAlimento.FRESCO, quantidade=-5,
            )
        msgs = [e["msg"] for e in exc.value.errors()]
        assert any("greater than 0" in m for m in msgs)

    def test_quantidade_zero_rejeitada(self):
        """Zero também não passa — gt=0, não gte=0."""
        with pytest.raises(ValidationError):
            ItemAlimentar(
                user_id="u1", nome="Maçã",
                categoria=CategoriaAlimento.FRESCO, quantidade=0,
            )

    def test_nome_apenas_numeros_rejeitado(self):
        """'12345' não é nome de alimento — validator customizado rejeita."""
        with pytest.raises(ValidationError) as exc:
            ItemAlimentar(
                user_id="u1", nome="12345",
                categoria=CategoriaAlimento.FRESCO, quantidade=1,
            )
        msgs = str(exc.value)
        assert "número" in msgs.lower() or "numerico" in msgs.lower() or "números" in msgs.lower()

    def test_nome_vazio_rejeitado(self):
        """Nome vazio viola min_length=2."""
        with pytest.raises(ValidationError):
            ItemAlimentar(
                user_id="u1", nome="",
                categoria=CategoriaAlimento.FRESCO, quantidade=1,
            )

    def test_nome_um_char_rejeitado(self):
        """Um único caractere também viola min_length=2."""
        with pytest.raises(ValidationError):
            ItemAlimentar(
                user_id="u1", nome="A",
                categoria=CategoriaAlimento.FRESCO, quantidade=1,
            )

    def test_validade_antes_da_compra_rejeitada(self):
        """Validade anterior à compra: model_validator rejeita."""
        with pytest.raises(ValidationError) as exc:
            ItemAlimentar(
                user_id="u1", nome="Leite",
                categoria=CategoriaAlimento.LATICINIOS, quantidade=1,
                data_compra=date(2026, 6, 1),
                data_validade=date(2026, 1, 1),
            )
        assert "validade" in str(exc.value).lower() or "data" in str(exc.value).lower()

    def test_multiplos_erros_simultaneos(self):
        """Pydantic coleta TODOS os erros de uma vez — não para no primeiro."""
        with pytest.raises(ValidationError) as exc:
            ItemAlimentar(
                nome="",          # erro 1: vazio
                categoria=CategoriaAlimento.FRESCO,
                quantidade=-1,    # erro 2: negativo
            )
        assert len(exc.value.errors()) >= 2
