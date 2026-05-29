"""
Camada de acesso ao banco.
Conecta Pydantic (validação) + Embeddings (vetores) + pgvector (armazenamento).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from models.alimento import ItemAlimentar

DSN = "dbname=gestor_alimentos user=lucas-parente port=5433"
_modelo = None


def modelo_embedding():
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _modelo


def conectar():
    conn = psycopg2.connect(DSN)
    register_vector(conn)   # ensina o psycopg2 a entender o tipo vector
    return conn


# ──────────────────────────────────────────────────
# INSERIR
# Recebe um ItemAlimentar já validado pelo Pydantic,
# gera o embedding do nome e salva tudo no banco.
# ──────────────────────────────────────────────────
def _texto_para_embedding(item: ItemAlimentar) -> str:
    """
    Monta o texto que será embedado. Incluir categoria dá contexto ao modelo —
    'Maçã Fuji, categoria: fresco' fica no cluster alimentar, não no cluster Apple/tech.
    """
    return f"{item.nome}, categoria: {item.categoria.value}"


def inserir_alimento(item: ItemAlimentar) -> str:
    vetor = modelo_embedding().encode(_texto_para_embedding(item))

    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO alimentos
                    (id, user_id, nome, categoria, quantidade, unidade,
                     data_compra, data_validade, embedding)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                item.id,
                item.user_id,
                item.nome,
                item.categoria.value,
                item.quantidade,
                item.unidade,
                item.data_compra,
                item.data_validade,
                vetor,
            ))
    return item.id


# ──────────────────────────────────────────────────
# BUSCAR POR SIMILARIDADE
# Recebe um texto livre, gera o embedding da pergunta
# e busca os N alimentos mais próximos — sempre
# filtrado pelo user_id (isolamento multi-tenant).
# ──────────────────────────────────────────────────
def buscar_similares(texto: str, user_id: str, limite: int = 5) -> list[dict]:
    vetor_pergunta = modelo_embedding().encode(texto)

    with conectar() as conn:
        register_vector(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    nome,
                    categoria,
                    quantidade,
                    unidade,
                    data_validade,
                    1 - (embedding <=> %s::vector) AS similaridade
                FROM alimentos
                WHERE user_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (vetor_pergunta, user_id, vetor_pergunta, limite))
            return cur.fetchall()


# ──────────────────────────────────────────────────
# LISTAR TUDO (para inspecionar o banco)
# ──────────────────────────────────────────────────
def listar_alimentos(user_id: str) -> list[dict]:
    with conectar() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, nome, categoria, quantidade, unidade, data_validade
                FROM alimentos
                WHERE user_id = %s
                ORDER BY nome
            """, (user_id,))
            return cur.fetchall()


def limpar_alimentos(user_id: str) -> int:
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM alimentos WHERE user_id = %s", (user_id,))
            return cur.rowcount
