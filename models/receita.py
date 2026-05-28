from pydantic import BaseModel, Field, field_validator
from typing import Optional
import uuid


class IngredienteReceita(BaseModel):
    """Um ingrediente dentro de uma receita — referencia o nome, não o ID do item."""
    nome: str = Field(..., min_length=2)
    quantidade: float = Field(..., gt=0)
    unidade: str = Field(..., min_length=1)


class Receita(BaseModel):
    """
    Receita pertence a um usuário. user_id garante que um usuário
    não veja as receitas de outro no banco vetorial.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="Dono da receita. Obrigatório.")

    nome: str = Field(..., min_length=3, max_length=120)
    ingredientes: list[IngredienteReceita] = Field(..., min_length=1)
    modo_preparo: Optional[str] = None
    tempo_preparo_minutos: Optional[int] = Field(None, gt=0)

    # Texto que vai ser vetorizado para busca semântica no pgvector
    descricao_para_embedding: Optional[str] = None

    @field_validator("ingredientes")
    @classmethod
    def sem_ingredientes_duplicados(cls, v: list[IngredienteReceita]) -> list[IngredienteReceita]:
        nomes = [i.nome.lower() for i in v]
        if len(nomes) != len(set(nomes)):
            raise ValueError("A receita contém ingredientes duplicados.")
        return v
