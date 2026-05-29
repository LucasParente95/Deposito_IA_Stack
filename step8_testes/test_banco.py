"""
Step 7 — Testes pgvector: inserção, busca e isolamento multi-tenant

O teste mais importante aqui não é "salvou corretamente".
É "Bob não vê os dados da Ana" — o isolamento é o coração do sistema.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date
from models.alimento import ItemAlimentar, CategoriaAlimento
from step3_pgvector.banco import inserir_alimento, buscar_similares, listar_alimentos, limpar_alimentos

USER_A = "test-isolamento-a"
USER_B = "test-isolamento-b"


@pytest.fixture(autouse=True)
def limpar_antes_e_depois():
    """Garante banco limpo antes e depois de cada teste."""
    limpar_alimentos(USER_A)
    limpar_alimentos(USER_B)
    yield
    limpar_alimentos(USER_A)
    limpar_alimentos(USER_B)


def _criar_item(user_id, nome, categoria=CategoriaAlimento.FRESCO, qtd=1):
    return ItemAlimentar(user_id=user_id, nome=nome, categoria=categoria, quantidade=qtd)


# ── INSERÇÃO ──────────────────────────────────────────────────────

class TestInsercao:
    def test_insere_e_lista(self):
        item = _criar_item(USER_A, "Banana Teste")
        inserir_alimento(item)
        lista = listar_alimentos(USER_A)
        nomes = [i["nome"] for i in lista]
        assert "Banana Teste" in nomes

    def test_insercao_duplicada_ignorada(self):
        """ON CONFLICT DO NOTHING: inserir o mesmo id duas vezes não duplica."""
        item = _criar_item(USER_A, "Manga")
        inserir_alimento(item)
        inserir_alimento(item)
        lista = listar_alimentos(USER_A)
        assert len([i for i in lista if i["nome"] == "Manga"]) == 1

    def test_banco_vazio_retorna_lista_vazia(self):
        lista = listar_alimentos(USER_A)
        assert lista == []


# ── ISOLAMENTO MULTI-TENANT ───────────────────────────────────────

class TestIsolamento:
    def test_usuario_a_nao_ve_dados_do_b(self):
        """WHERE user_id = ? garante que A não vê dados de B."""
        inserir_alimento(_criar_item(USER_B, "Produto Secreto Do Bob"))
        lista_a = listar_alimentos(USER_A)
        nomes_a = [i["nome"] for i in lista_a]
        assert "Produto Secreto Do Bob" not in nomes_a

    def test_busca_semantica_isolada_por_user(self):
        """Mesma busca, user_id diferente → resultados diferentes."""
        inserir_alimento(_criar_item(USER_A, "Maçã Fuji", CategoriaAlimento.FRESCO))
        inserir_alimento(_criar_item(USER_B, "Frango Congelado", CategoriaAlimento.CONGELADO))

        resultados_a = buscar_similares("fruta", USER_A, limite=5)
        resultados_b = buscar_similares("fruta", USER_B, limite=5)

        nomes_a = [r["nome"] for r in resultados_a]
        nomes_b = [r["nome"] for r in resultados_b]

        assert "Maçã Fuji" in nomes_a
        assert "Maçã Fuji" not in nomes_b
        assert "Frango Congelado" not in nomes_a

    def test_limpar_user_a_nao_afeta_user_b(self):
        """DELETE WHERE user_id = A não toca nos dados de B."""
        inserir_alimento(_criar_item(USER_A, "Item de A"))
        inserir_alimento(_criar_item(USER_B, "Item de B"))

        limpar_alimentos(USER_A)

        assert listar_alimentos(USER_A) == []
        nomes_b = [i["nome"] for i in listar_alimentos(USER_B)]
        # .title() do Pydantic capitaliza cada palavra: "Item de B" → "Item De B"
        assert "Item De B" in nomes_b


# ── BUSCA SEMÂNTICA ───────────────────────────────────────────────

class TestBuscaSemantica:
    def test_busca_retorna_mais_similar_primeiro(self):
        inserir_alimento(_criar_item(USER_A, "Banana Prata", CategoriaAlimento.FRESCO))
        inserir_alimento(_criar_item(USER_A, "Frango Congelado", CategoriaAlimento.CONGELADO))

        resultados = buscar_similares("fruta tropical", USER_A, limite=2)
        assert resultados[0]["nome"] == "Banana Prata"

    def test_busca_usuario_sem_dados_retorna_vazio(self):
        resultados = buscar_similares("qualquer coisa", USER_A, limite=5)
        assert resultados == []

    def test_similaridade_entre_0_e_1(self):
        inserir_alimento(_criar_item(USER_A, "Leite", CategoriaAlimento.LATICINIOS))
        resultados = buscar_similares("laticínio", USER_A, limite=1)
        assert 0.0 <= float(resultados[0]["similaridade"]) <= 1.0
