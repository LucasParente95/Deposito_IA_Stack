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

## Sessão 2 — 2026-05-28 (segunda máquina — PC com Claude Code)

### O que foi construído

**Ambiente da segunda máquina configurado do zero:**
- Python packages instalados via `pip install --user`: pydantic, sentence-transformers, psycopg2-binary, pgvector, customtkinter, ollama
- PostgreSQL 16 instalado + porta alterada para 5433 (para coincidir com o notebook)
- pgvector instalado via `apt install postgresql-16-pgvector`
- Banco `gestor_alimentos` criado, extensão vector ativada, tabelas criadas, dados populados
- Ollama instalado + modelo `gemma3:4b` baixado (3.3GB) — escolha por qualidade em português
- pg_hba.conf ajustado para `trust` em conexões locais (ambiente de dev)

**Step 4 — RAG** ✅
- `step4_rag/rag.py` — lógica pura do pipeline:
  - `buscar_contexto(pergunta, user_id)` → chama `buscar_similares` do banco
  - `formatar_contexto(itens)` → transforma lista de alimentos em texto com relevância
  - `montar_prompt(pergunta, contexto)` → prompt completo para o LLM
  - `responder_com_rag(pergunta, user_id)` → pipeline completo, retorna resposta + itens usados
- `step4_rag/interface.py` — GUI CustomTkinter com 3 painéis lado a lado:
  - Painel 1: documentos recuperados do banco (com % de relevância)
  - Painel 2: prompt completo enviado ao Gemma 3
  - Painel 3: resposta gerada pelo LLM
  - Seletor de usuário (Ana / Bob) para demonstrar isolamento
  - Botões de perguntas de exemplo
  - Execução em thread separada (UI não trava durante chamada ao LLM)

### Decisões tomadas

- LLM escolhido: `gemma3:4b` via Ollama local — sem API externa, foco em português
- user_ids dos dados de teste: `user-ana-001` e `user-bob-002` (definidos no step3/testes.py)
- Isolamento multi-tenant confirmado: mesma pergunta, user_id diferente → resultados diferentes

### Observações pedagógicas

- O Gemma 3 **filtrou corretamente** os itens recuperados: perguntando "frutas", o banco devolveu Presunto e Frango com baixa relevância, mas o LLM os ignorou na resposta
- Pergunta sobre **validade**: o banco recupera por similaridade semântica (não sabe de datas), mas o LLM leu as datas no contexto e apontou os itens mais urgentes corretamente
- RAG desmistificado: é literalmente `busca_vetorial() + f"Esses são os alimentos: {contexto}"` → LLM. Não tem mágica.
- O isolamento ficou explícito na interface: trocar o usuário no dropdown muda completamente os documentos recuperados e a resposta gerada

### Próximos steps

- **Step 5 — FastAPI**: expor o pipeline RAG como uma rota HTTP (`POST /perguntar`)
- Rota receberá `{pergunta: str, user_id: str}` e retornará `{resposta: str, itens_usados: list}`

---

---

## Sessão 3 — 2026-05-28 (continuação no PC com Claude Code)

### O que foi construído

**Refatoração modular das interfaces:**
- Interfaces separadas por step foram removidas (step1/interface.py, step2/interface.py, geladeira.py, step4/interface.py)
- `interfaces/app.py` é agora a única interface — menu lateral com abas "Usar" e "Ver Código" em cada step
- Cada step delega para seu módulo:
  - `step1_pydantic/validador.py` — validar_item() com log campo a campo
  - `step2_embeddings/gerador.py` — gerar_embedding(), cor_dimensao()
  - `step3_pgvector/operacoes.py` — salvar_alimento(), cor_similaridade()
  - `step4_rag/rag.py` — responder_com_rag() (chamada correta, sem duplicação)
- Aba "Ver Código" em cada step: exibe o fonte real do módulo responsável + anotações pedagógicas
- Log campo a campo no painel Pydantic: mostra regra verificada, valor recebido, pass/fail por campo

**Step 5 — FastAPI** ✅
- `step5_fastapi/api.py` com 4 rotas:
  - POST /perguntar → responder_com_rag()
  - POST /alimentos → salvar_alimento()
  - GET /alimentos/{user_id} → listar_alimentos()
  - GET /buscar/{user_id} → buscar_similares()
- Painel Step 5 na interface: inicia/para o servidor uvicorn, cliente HTTP integrado, exibe JSON de resposta
- Servidor para automaticamente quando a janela é fechada
- `npm run docs` abre http://localhost:8000/docs (Swagger gerado automaticamente pelo FastAPI)

### Decisões tomadas

- CustomTkinter é suporte — não precisa ser explicado, apenas construído
- Interface unificada com abas "Usar" / "Ver Código" em vez de interfaces separadas
- Cada step tem seu próprio módulo de lógica — app.py é só apresentação
- FastAPI exposto na porta 8000; uvicorn gerenciado pela própria interface (subprocess)

### Observações pedagógicas

- A aba "Ver Código" torna o pipeline transparente: você vê o código que está rodando enquanto usa
- O painel FastAPI mostra que a API é literalmente a mesma função chamada de um jeito diferente
- HTTPException com código 422 usa o mesmo Pydantic ValidationError por baixo — consistência do stack

### Próximos steps

- **Step 6 — LangChain + MCP**: agente que usa as rotas FastAPI como ferramentas
- **Step 7 — Testes pytest**
- **Step 8 — Red Teaming + RLS**

---

## Sessão 4 — 2026-05-29 (Recuperação após travamento)

### O que foi construído

**Painel Step 6 — MCP — REPARADO** ✅
- O painel havia sido adicionado mas tinha import assíncrono quebrado (`asyncio.run()` no tkinter)
- Corrigei `_mcp_atualizar_schemas()`: agora constrói os schemas MCP manualmente sem tentar chamar funções async do servidor
- Corrigei `_mcp_chamar()`: agora chama as funções originais (buscar_similares, listar_alimentos, responder_com_rag) diretamente, sem MCP
- O painel mostra lado a lado: schema LangChain vs schema MCP vs resultado da execução

**Configuração de Contexto**
- Ativado `autoCompactEnabled` em `~/.claude/settings.json` para compactação automática quando contexto fica cheio

### Decisões tomadas

- Não tentar chamar o servidor MCP (que é um processo separado) diretamente da interface
- Chamar as funções Python originais de forma síncrona é mais simples para o painel educacional
- O painel MCP agora demonstra o contraste entre os 3 formatos (LangChain @tool, FastAPI, MCP) sem executar via servidor

### Observações pedagógicas

- A confusão aconteceu porque o servidor MCP é assíncrono/em processo separado, mas a interface precisa de chamadas síncronas
- A solução foi "fake" MCP: executa as ferramentas direto, mas mostra como seria no protocolo real
- Isso é pedagogicamente útil: você vê o schema MCP ao lado da execução

### Próximos steps

- Testar o painel MCP na interface (rodar a app e verificar se os schemas e execução funcionam)
- Depois disso: próximo step pedagógico (testes, security, etc)

---

<!-- Nova sessão: copie o bloco abaixo e preencha -->
<!--
## Sessão N — AAAA-MM-DD

### O que foi construído

### Decisões tomadas

### Observações pedagógicas

### Próximos steps
-->
