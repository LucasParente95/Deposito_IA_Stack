"""
Step 7 — Testes de Embeddings

Documenta o comportamento do modelo de embeddings:
  - Que o vetor tem as dimensões certas
  - Que textos similares ficam próximos
  - Que textos sem relação ficam distantes
  - Casos ambíguos onde o modelo surpreende
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from step2_embeddings.gerador import gerar_embedding, calcular_similaridade


# ── ESTRUTURA DO VETOR ────────────────────────────────────────────

class TestEstruturaVetor:
    def test_dimensoes_corretas(self):
        """O modelo deve sempre gerar exatamente 384 dimensões."""
        r = gerar_embedding("maçã")
        assert r["dimensoes"] == 384

    def test_vetor_nao_vazio(self):
        r = gerar_embedding("banana")
        assert len(r["vetor"]) == 384

    def test_metadados_presentes(self):
        r = gerar_embedding("leite")
        assert "minimo" in r
        assert "maximo" in r
        assert r["minimo"] < r["maximo"]

    def test_mesmo_texto_mesmo_vetor(self):
        """Embedding é determinístico — mesmo texto, mesmo vetor."""
        v1 = gerar_embedding("frango")["vetor"]
        v2 = gerar_embedding("frango")["vetor"]
        sim = calcular_similaridade(v1, v2)
        assert sim > 0.9999


# ── SIMILARIDADE: O QUE DEVERIA FUNCIONAR ─────────────────────────

class TestSimilaridadeEsperada:
    def test_identico_tem_similaridade_maxima(self):
        v = gerar_embedding("maçã")["vetor"]
        assert calcular_similaridade(v, v) > 0.9999

    def test_variacao_do_mesmo_produto_similar(self):
        """'leite integral' e 'leite desnatado' devem ser próximos."""
        v1 = gerar_embedding("leite integral")["vetor"]
        v2 = gerar_embedding("leite desnatado")["vetor"]
        assert calcular_similaridade(v1, v2) > 0.80

    def test_mesmo_ingrediente_cru_e_cozido_similar(self):
        """'frango cru' e 'frango assado' — o modelo entende que é o mesmo ingrediente."""
        v1 = gerar_embedding("frango cru")["vetor"]
        v2 = gerar_embedding("frango assado")["vetor"]
        assert calcular_similaridade(v1, v2) > 0.85

    def test_sinonimos_de_validade_similares(self):
        """'vencido' e 'expirado' devem ser próximos semanticamente."""
        v1 = gerar_embedding("vencido")["vetor"]
        v2 = gerar_embedding("expirado")["vetor"]
        assert calcular_similaridade(v1, v2) > 0.75

    def test_categoria_melhora_similaridade(self):
        """'Maçã Fuji, categoria: fresco' deve ficar mais próximo de 'fruta'
        do que só 'Maçã Fuji' — validação da nossa estratégia de embedding."""
        v_fruta   = gerar_embedding("fruta")["vetor"]
        v_sem_cat = gerar_embedding("Maçã Fuji")["vetor"]
        v_com_cat = gerar_embedding("Maçã Fuji, categoria: fresco")["vetor"]
        sim_sem = calcular_similaridade(v_fruta, v_sem_cat)
        sim_com = calcular_similaridade(v_fruta, v_com_cat)
        assert sim_com > sim_sem, (
            f"Com categoria ({sim_com:.3f}) deveria ser maior que sem ({sim_sem:.3f})"
        )


# ── CASOS AMBÍGUOS: ONDE O MODELO SURPREENDE ─────────────────────

class TestCasosAmbiguos:
    def test_maca_fuji_vs_fruta_baixa_sem_contexto(self):
        """'Maçã Fuji' sozinha tem similaridade baixa com 'fruta'
        por causa da associação com Apple (empresa) no treinamento."""
        v1 = gerar_embedding("Maçã Fuji")["vetor"]
        v2 = gerar_embedding("fruta")["vetor"]
        sim = calcular_similaridade(v1, v2)
        # documentamos que é baixo — não é um bug, é comportamento esperado sem contexto
        assert sim < 0.60, f"Esperado baixo sem contexto, mas foi {sim:.3f}"

    def test_alimento_vs_ferramenta_distantes(self):
        """'banana' e 'martelo' devem ter baixa similaridade."""
        v1 = gerar_embedding("banana")["vetor"]
        v2 = gerar_embedding("martelo")["vetor"]
        assert calcular_similaridade(v1, v2) < 0.50

    def test_comida_vs_construcao_muito_distantes(self):
        """'frango congelado' e 'cimento' — nenhuma relação semântica."""
        v1 = gerar_embedding("frango congelado")["vetor"]
        v2 = gerar_embedding("cimento")["vetor"]
        assert calcular_similaridade(v1, v2) < 0.40
