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

| Step | Foco                                                    | O que você vai entender                                           | Status       |
| ---- | ------------------------------------------------------- | ----------------------------------------------------------------- | ------------ |
| 1    | Modelos Pydantic com `user_id` obrigatório              | Como validar dados na entrada do sistema                          | ✅ concluído |
| 2    | Embeddings: texto → vetor                               | Por que "maçã" e "fruta" ficam próximos no espaço vetorial        | ✅ concluído |
| 3    | pgvector: armazenar e buscar vetores no banco           | Como a busca semântica funciona com filtro de `user_id`           | ✅ concluído |
| 4    | RAG: busca vetorial + LLM = resposta com contexto       | Por que o modelo responde melhor quando tem documentos relevantes | ✅ concluído |
| 5    | Rota FastAPI: texto livre → LLM → Pydantic → banco      | Como expor tudo isso como uma API                                 | ✅ concluído |
| 6    | MCP: servidor Model Context Protocol                    | Como expor ferramentas para qualquer modelo de IA (padrão aberto) | ✅ concluído |
| 7    | Agente LangChain + LangGraph StateGraph                 | Como um agente usa ferramentas para raciocinar em loop            | ✅ concluído |
| 8    | Testes pytest: texto perfeito / ambíguo / lixo total    | Como garantir que o sistema se comporta nos casos extremos        | ✅ concluído |
| 9.1  | OWASP LLM01/03 — Defesa contra RAG Poisoning            | Sanitização e filtro antes do banco vetorial (Pydantic + FastAPI) | ✅ concluído |
| 9.2  | OWASP LLM02 — Defesa contra Saída Insegura              | Middleware que valida o contrato JSON da resposta do LLM          | ✅ concluído |
| 9.3  | OWASP LLM04 — Defesa contra Denial of Wallet            | Rate limiting por rota para proteger cotas de API                 | ✅ concluído |

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

> **AGENTE:** ao final de cada sessão, antes de encerrar, **sempre atualize o `DIARIO.md`**.
> Não espere o usuário pedir. É sua responsabilidade garantir que o próximo agente
> (nesta ou em outra máquina) encontre o contexto completo e atualizado.

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

## A Regra de Ouro — Nunca Viole

> **É terminantemente PROIBIDO** gerar o sistema inteiro de uma vez ("vibe coding").
> Cada turno deve construir **um único componente isolado**.

Se você se pegar escrevendo código que o usuário ainda não solicitou explicitamente,
**pare imediatamente**. Refatore sua resposta para conter apenas o que foi pedido.

## Protocolo Obrigatório para Cada Passo

Para cada passo solicitado pelo usuário, a resposta **deve** conter exatamente:

1. **Conceito Clássico** — Explicação em no máximo **2 parágrafos**, como se o leitor
   fosse um engenheiro iniciante. Sem jargão desnecessário.

2. **Código Isolado** — Apenas o código daquele componente. Nenhuma linha a mais.

3. **Como Testar Visualmente** — Instrução clara de como validar aquele componente
   específico no painel CustomTkinter.

4. **Parar e Aguardar** — Após entregar o passo, **não sugira o próximo código**.
   Aguarde a validação explícita do usuário antes de qualquer avanço.
