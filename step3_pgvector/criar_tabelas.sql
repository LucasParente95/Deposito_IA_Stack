-- Tabela de alimentos com coluna vetorial
CREATE TABLE IF NOT EXISTS alimentos (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       TEXT NOT NULL,
    nome          TEXT NOT NULL,
    categoria     TEXT NOT NULL,
    quantidade    FLOAT NOT NULL,
    unidade       TEXT NOT NULL DEFAULT 'unidade',
    data_compra   DATE,
    data_validade DATE,
    embedding     vector(384)          -- as 384 coordenadas do significado
);

-- Índice vetorial: acelera a busca por similaridade
-- ivfflat = algoritmo de busca aproximada (rápido em tabelas grandes)
CREATE INDEX IF NOT EXISTS idx_alimentos_embedding
    ON alimentos USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- Índice comum no user_id: garante que o filtro multi-tenant seja rápido
CREATE INDEX IF NOT EXISTS idx_alimentos_user_id
    ON alimentos (user_id);

-- Tabela de receitas com coluna vetorial
CREATE TABLE IF NOT EXISTS receitas (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  TEXT NOT NULL,
    nome                     TEXT NOT NULL,
    ingredientes             JSONB NOT NULL,
    modo_preparo             TEXT,
    tempo_preparo_minutos    INT,
    descricao_para_embedding TEXT,
    embedding                vector(384)
);

CREATE INDEX IF NOT EXISTS idx_receitas_embedding
    ON receitas USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

CREATE INDEX IF NOT EXISTS idx_receitas_user_id
    ON receitas (user_id);
