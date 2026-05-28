-- Execute uma vez como superusuário postgres:
-- sudo -u postgres psql -p 5433 -f step3_pgvector/setup_banco.sql

-- Cria o usuário da aplicação (sem senha por enquanto — ambiente local)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lucas-parente') THEN
        CREATE ROLE "lucas-parente" LOGIN;
    END IF;
END
$$;

-- Cria o banco
SELECT 'CREATE DATABASE gestor_alimentos OWNER "lucas-parente"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gestor_alimentos')\gexec

-- Conecta ao banco e ativa o pgvector
\c gestor_alimentos
CREATE EXTENSION IF NOT EXISTS vector;
GRANT ALL ON SCHEMA public TO "lucas-parente";

\echo '✅ Banco gestor_alimentos criado com pgvector ativado.'
