from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
from datetime import date
from enum import Enum
import uuid


class FonteEntrada(str, Enum):
    """De onde veio o dado: PDF ou formulário manual."""
    PDF = "pdf"
    FORMULARIO = "formulario"


class CategoriaAlimento(str, Enum):
    FRESCO = "fresco"           # frutas, verduras, carnes sem processamento
    EMBUTIDO = "embutido"       # salsicha, mortadela, presunto
    CONGELADO = "congelado"     # itens que exigem freezer
    SEM_CONSERVANTE = "sem_conservante"  # naturais, orgânicos
    ENLATADO = "enlatado"
    LATICINIOS = "laticinios"
    OUTRO = "outro"


class ItemAlimentar(BaseModel):
    """
    Modelo central. Representa qualquer alimento no sistema.
    user_id é obrigatório — é o que garante o isolamento multi-tenant.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID do dono deste registro. Nunca pode ser nulo.")

    nome: str = Field(..., min_length=2, max_length=100)
    categoria: CategoriaAlimento
    quantidade: float = Field(..., gt=0, description="Deve ser maior que zero")
    unidade: Literal["kg", "g", "L", "ml", "unidade", "cx"] = "unidade"

    data_compra: Optional[date] = None
    data_validade: Optional[date] = None

    fonte: FonteEntrada = FonteEntrada.FORMULARIO

    # Campos que chegam crus do PDF — texto livre antes de ser processado
    texto_original_pdf: Optional[str] = Field(
        None,
        description="Trecho bruto extraído do PDF, para rastreabilidade"
    )

    @field_validator("nome")
    @classmethod
    def nome_nao_pode_ser_numerico(cls, v: str) -> str:
        if v.strip().isdigit():
            raise ValueError("Nome do alimento não pode ser apenas números.")
        return v.strip().title()

    @model_validator(mode="after")
    def validade_depois_da_compra(self) -> "ItemAlimentar":
        if self.data_compra and self.data_validade:
            if self.data_validade < self.data_compra:
                raise ValueError(
                    f"data_validade ({self.data_validade}) não pode ser "
                    f"anterior à data_compra ({self.data_compra})."
                )
        return self

    @model_validator(mode="after")
    def pdf_exige_texto_original(self) -> "ItemAlimentar":
        if self.fonte == FonteEntrada.PDF and not self.texto_original_pdf:
            raise ValueError(
                "Quando a fonte é 'pdf', o campo texto_original_pdf é obrigatório "
                "para rastreabilidade."
            )
        return self
