# Diário de Sessões

> Lido pelo Claude no início de cada conversa para retomar o contexto.
> Atualizado ao final de cada sessão com o que foi feito, decidido e o que vem a seguir.

---

## Sessão 1 — 2026-05-28

### O que foi construído

**Step 1 — Pydantic** ✅
- Modelos `ItemAlimentar` e `Receita` em `models/`
- `user_id` obrigatório em ambos — base do isolamento multi-tenant
- Validadores: nome numérico rejeitado, validade antes da compra rejeitada, PDF sem rastreabilidade rejeitado, ingredientes duplicados rejeitados
- Interface visual em `step1_pydantic/interface.py` com 3 abas (formulário, arquivo/texto, receita)
- Testes em `step1_pydantic/testes.py` — 6 casos cobrindo dados perfeitos, ambíguos e lixo total

**Step 2 — Embeddings** ✅
- Biblioteca: `sentence-transformers` com modelo `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensões, multilíngue)
- Script exploratório em `step2_embeddings/explorar.py`
- Interface visual em `step2_embeddings/interface.py` com 3 abas:
  - Vetor Bruto: 384 quadradinhos coloridos (azul=positivo, vermelho=negativo), hover mostra o valor
  - Comparar: barras de progresso ordenadas por similaridade
  - Pares Suspeitos: testa onde o modelo acerta ou surpreende

**Step 3 — pgvector** ✅
- PostgreSQL 16 + extensão pgvector instalados
- Banco `gestor_alimentos` criado com usuário `lucas-parente`, porta 5433
- Tabelas `alimentos` e `receitas` com coluna `embedding vector(384)` e índice `ivfflat`
- `step3_pgvector/banco.py`: funções `inserir_alimento`, `buscar_similares`, `listar_alimentos`, `limpar_alimentos`
- `step3_pgvector/testes.py`: dois usuários (Ana e Bob) com isolamento comprovado
- Interface combinada Steps 2+3 em `interfaces/geladeira.py` com 4 abas:
  - Adicionar Item (formulário)
  - Texto/Arquivo (chunking: fatia por vírgula/linha, embedding de cada chunk, salva tudo)
  - Minha Geladeira (lista do banco filtrada por user_id)
  - Busca Semântica (linguagem natural → vetor → banco → resultados com barras)

### Decisões tomadas

- Isolamento multi-tenant via `user_id` na coluna (não schema por tenant nem RLS por enquanto)
- RLS (Row Level Security) fica para o Step 8 (Red Teaming) como upgrade de segurança
- Interfaces separadas por step + pasta `interfaces/` para as combinadas
- `sys.path.insert` nos arquivos de subpastas para encontrar `models/` na raiz
- Modelo de embedding multilíngue para suportar português sem degradação severa
- Porta 5433 (não a padrão 5432) — PostgreSQL local configurado assim

### Observações pedagógicas

- "Maçã Fuji" teve similaridade baixa com "fruta" por influência da Apple (empresa) no modelo
- `leite integral ↔ leite desnatado` = 95.6% — modelo bom em variações do mesmo produto
- `frango cru ↔ frango assado` = 97.5% — modelo entende que é o mesmo ingrediente
- O isolamento multi-tenant ficou visível: mesma busca, user_id diferente, resultados diferentes

### Próximos steps

- **Step 4 — RAG**: conectar busca vetorial com LLM para responder perguntas com contexto do banco
- **Step 5 — FastAPI**: expor o pipeline como API REST
- **Step 6 — LangChain + MCP**: agente que usa ferramentas para raciocinar
- **Step 7 — Testes pytest**
- **Step 8 — Red Teaming + RLS**

### Contexto do usuário

- Não é desenvolvedor — quer entender o propósito e funcionamento das ferramentas
- Background em banco de dados (SQL, modelagem) — analogias com SQL funcionam bem
- Objetivo: replicar esses padrões em outros projetos, melhorar agentes de IA, se posicionar no mercado
- Usa Syncthing para sincronizar entre computadores
- Prefere CustomTkinter para interfaces visuais
- Gosta de ver os conceitos em ação antes do código

---

<!-- Nova sessão: copie o bloco abaixo e preencha -->
<!--
## Sessão N — AAAA-MM-DD

### O que foi construído

### Decisões tomadas

### Observações pedagógicas

### Próximos steps
-->
