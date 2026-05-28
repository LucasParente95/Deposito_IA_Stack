# Gestor de Alimentos Domésticos — SaaS Multi-tenant

## Propósito deste projeto

Este é um projeto **pedagógico**, não um produto. O objetivo é observar ferramentas em ação:
Pydantic, Embeddings, pgvector, RAG, LangChain, FastAPI, MCP.

A mentalidade do aprendiz aqui é a do **engenheiro que supervisiona a obra**: ele não quer aprender a subir parede, mas quer entender o que o pedreiro está fazendo, por que está fazendo assim, o que acontece quando algo dá errado, e o que os materiais permitem ou limitam.

## O que NÃO é o objetivo

- Aprender a codar
- Decorar sintaxe
- Virar desenvolvedor Python

## O que É o objetivo

- Entender o que acontece quando pedimos certas estruturas de dados para a IA
- Ver como o Pydantic reage a dados malformados, ambíguos ou absurdos
- Entender o que é um embedding e por que texto vira número
- Ver como o RAG conecta busca vetorial com geração de resposta
- Observar como a segurança se manifesta na arquitetura (não no "pedido educado")
- Sentir o peso das decisões de design antes de precisar tomá-las em produção

## Stack

- **Pydantic** — validação e tipagem (a fronteira do sistema)
- **Embeddings** — transformar texto em vetores numéricos para busca semântica
- **PostgreSQL + pgvector** — banco que armazena e busca vetores
- **RAG** — Retrieval-Augmented Generation: buscar contexto relevante antes de responder
- **FastAPI** — camada de API
- **LangChain** — agente de raciocínio com ferramentas
- **MCP** — protocolo de contexto para o modelo

## Roteiro dos Baby Steps

| Step | Foco | O que você vai entender | Status |
|------|------|------------------------|--------|
| 1 | Modelos Pydantic com `user_id` obrigatório | Como validar dados na entrada do sistema | ✅ concluído |
| 2 | Embeddings: texto → vetor | Por que "maçã" e "fruta" ficam próximos no espaço vetorial | ✅ concluído |
| 3 | pgvector: armazenar e buscar vetores no banco | Como a busca semântica funciona com filtro de `user_id` | ✅ concluído |
| 4 | RAG: busca vetorial + LLM = resposta com contexto | Por que o modelo responde melhor quando tem documentos relevantes | pendente |
| 5 | Rota FastAPI: texto livre → LLM → Pydantic → banco | Como expor tudo isso como uma API | pendente |
| 6 | Agente LangChain + servidor MCP para alertas | Como um agente usa ferramentas para raciocinar | pendente |
| 7 | Testes pytest: texto perfeito / ambíguo / lixo total | Como garantir que o sistema se comporta nos casos extremos | pendente |
| 8 | Red Teaming: Prompt Injection + isolamento multi-tenant | Por que segurança está no banco, não no prompt | pendente |

## Continuidade entre sessões e máquinas

Este projeto é sincronizado via **Syncthing** entre computadores e versionado no **Git**.

**Ao iniciar qualquer sessão**, leia obrigatoriamente:
1. `DIARIO.md` — resumo de tudo que foi construído, decisões tomadas e próximos passos
2. O status do roteiro acima — para saber qual step está em andamento

**Ao encerrar qualquer sessão**, atualize o `DIARIO.md` com:
- O que foi construído nesta sessão
- Decisões que foram tomadas e por quê
- Observações pedagógicas relevantes (o que surpreendeu, o que confirmou o esperado)
- O próximo passo concreto

O diário é a memória persistente do projeto. Sem ele, cada sessão começa do zero.

## Regra de Ouro

Desenvolvimento pedagógico: **um componente por vez**.
- Explicar o conceito brevemente
- Gerar apenas o código daquele componente
- Dizer como testar e o que observar

## Exemplos de experimentos planejados

- Pydantic: dados perfeitos, ambíguos ("comprei maçã e pera"), lixo total ("tijolo e cimento")
- Embeddings: visualizar a distância entre "leite integral" e "leite desnatado" vs "cerveja"
- RAG: perguntar "o que tenho vencendo essa semana?" e ver o sistema buscar no banco antes de responder
- Red Teaming: Prompt Injection tentando ver dados de outro tenant — falha no `WHERE user_id = ?`

## Segurança (princípio central)

A segurança **não está no prompt**. Está na arquitetura:
- `user_id` obrigatório em todos os modelos
- Toda busca vetorial filtrada por `user_id` no banco
- Prompt Injection não consegue contornar um `WHERE user_id = ?` em SQL
