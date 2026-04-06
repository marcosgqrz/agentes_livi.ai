# Escopo Detalhado do Projeto — Agentes Livi.AI

## 1. Visão Geral

**Nome do Projeto**: Agentes Livi.AI — Orquestrador Multi-Agente de Produto Digital

**Objetivo**: Plataforma de inteligência artificial que simula um time completo de produto digital. Ao receber uma descrição de produto, o sistema coordena 10 agentes especializados — distribuídos em Design, Engenharia e Qualidade/Infra — que trabalham de forma sequencial e paralela para entregar artefatos prontos: identidade de marca, wireframes, design system, arquitetura técnica, código funcional, testes e pipelines de CI/CD.

**Proposta de Valor**: Eliminar a fricção de orquestrar múltiplos profissionais e ferramentas na fase inicial de produtos digitais, reduzindo de semanas para minutos a geração de entregáveis de alta qualidade e coerência interna.

---

## 2. Problema que Resolve

| Dor | Impacto Atual | Solução do Projeto |
|-----|---------------|-------------------|
| Time inicial de produto custa alto e demora semanas | Alto custo de contratação + ramp-up | 10 agentes IA executando em minutos |
| Falta de coerência entre design e engenharia | Retrabalho constante | Contexto compartilhado entre todos os agentes |
| Dificuldade de documentar decisões de produto | Conhecimento tácito perdido | Cada execução é persistida no banco de dados |
| Prototipagem lenta para validação de ideias | Time-to-market alto | Planos pré-configurados (ex: `quick_ui`, `design_only`) |

---

## 3. Escopo Funcional

### 3.1 Agentes Especializados (10 agentes)

#### Design & Branding (4 agentes)
| Agente | Responsabilidades | Entregáveis |
|--------|------------------|-------------|
| **Brand Designer** | Posicionamento, identidade visual, paleta de cores, tipografia, brand voice | Guia de marca completo |
| **UX Designer** | Personas, wireframes, arquitetura da informação, fluxos de usuário | Blueprints de UX |
| **UI Designer** | Design system, tokens, telas em alta fidelidade, handoff para devs | Componentes e especificações |
| **UX Writer** | Microcopy, mensagens do sistema, onboarding, textos de interface | Biblioteca de conteúdo |

#### Engenharia (4 agentes)
| Agente | Responsabilidades | Entregáveis |
|--------|------------------|-------------|
| **Tech Lead** | Decisões de arquitetura, stack tecnológico, modelos de dados, APIs, segurança | ADRs e arquitetura técnica |
| **Frontend Dev** | React/Next.js, TypeScript, Tailwind, componentes, acessibilidade | Código frontend funcional |
| **Backend Dev** | Node.js/Fastify, APIs REST, autenticação, banco de dados | Código backend funcional |
| **Mobile Dev** | React Native/Expo, iOS/Android, offline-first, publicação nas lojas | Código mobile funcional |

#### Qualidade & Infraestrutura (2 agentes)
| Agente | Responsabilidades | Entregáveis |
|--------|------------------|-------------|
| **QA Engineer** | Planos de teste, E2E (Playwright), performance (k6), bug reports | Suite de testes |
| **DevOps Engineer** | CI/CD (GitHub Actions), Docker, Terraform, AWS, monitoramento | Pipelines e IaC |

---

### 3.2 Planos de Execução

| Plano | Agentes Envolvidos | Caso de Uso |
|-------|--------------------|-------------|
| `full_product` | Todos os 10 agentes | Produto completo do zero |
| `mobile_app` | Brand, UX, UI, UX Writer, Tech Lead, Mobile Dev, QA | App mobile completo |
| `design_only` | Brand, UX, UI, UX Writer | Apenas design e identidade |
| `dev_only` | Tech Lead, Frontend, Backend, QA, DevOps | Apenas engenharia |
| `quick_ui` | UX, UI, Frontend | UI rápida para validação |
| `custom` | Seleção manual de agentes | Necessidades específicas |

---

### 3.3 Interfaces de Usuário

#### CLI (Command-Line Interface)
```bash
python main.py new-project "Nome" --description "..."
python main.py run <PROJECT_ID> "tarefa" -t full_product
python main.py status <TASK_ID>
python main.py agents
python main.py list-projects
```

#### Interface Web (Flask)
- Seleção de squad (Criação, Desenvolvimento, Delivery)
- Formulário de briefing do produto
- Acompanhamento em tempo real da execução dos agentes
- Visualização dos artefatos gerados
- Geração e download de builds estáticas

---

### 3.4 Funcionalidades de Suporte

- **Classificador de Tarefas**: Detecta automaticamente o tipo de tarefa por palavras-chave e sugere o plano de execução adequado
- **Contexto Persistente de Projeto**: Decisões de marca e arquitetura são reutilizadas em tarefas futuras do mesmo projeto
- **PixelBridge**: Visualização dos agentes trabalhando como personagens em escritório pixel art (integração com pixel-agents-standalone)
- **Deployer**: Extrai blocos de código dos outputs e gera builds estáticas servidas em `/static/builds/<run_id>/`
- **Métricas de Execução**: Rastreamento de tokens consumidos, tempo de execução e status por agente

---

## 4. Escopo Técnico

### 4.1 Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   Interfaces                         │
│          CLI (main.py) │ Web (Flask/app.py)          │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│               Orquestrador (orchestrator.py)         │
│  - Gerencia fases de execução                        │
│  - Execução paralela via ThreadPoolExecutor          │
│  - Passagem de contexto entre agentes                │
└──────┬──────────────────────────────────┬────────────┘
       │                                  │
┌──────▼────────┐                ┌────────▼──────────┐
│  10 Agentes   │                │  Banco de Dados   │
│  (BaseAgent)  │                │  (Supabase)       │
│  + Prompts MD │                │  Projetos/Tarefas │
└──────┬────────┘                │  Execuções        │
       │                         └───────────────────┘
┌──────▼────────┐
│  Anthropic    │
│  Claude API   │
│  (Sonnet 4.6) │
└───────────────┘
```

### 4.2 Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Python 3.12 |
| IA | Anthropic Claude (claude-sonnet-4-6) |
| Web Framework | Flask 3.x |
| Servidor de Produção | Gunicorn (gthread, 2 workers, 4 threads) |
| Banco de Dados | Supabase (PostgreSQL) |
| Validação de Dados | Pydantic 2.x |
| Containerização | Docker (python:3.12-slim) |
| Deploy | Railway.app |
| Testes | pytest + unittest.mock |

### 4.3 Modelo de Dados (Supabase)

| Tabela | Descrição |
|--------|-----------|
| `projects` | Projetos com contexto de marca e stack |
| `tasks` | Tarefas com status e plano de execução |
| `agent_executions` | Log de cada agente: input, output, tokens, tempo |
| `task_results` | Resultado consolidado da tarefa |
| `project_context` | Contexto persistente reutilizável |
| `execution_plans` | Templates de workflow por tipo de produto |

### 4.4 Configurações de Sistema

| Parâmetro | Valor Padrão |
|-----------|-------------|
| Modelo Claude | claude-sonnet-4-6 |
| Max tokens por agente | 4.096 |
| Agentes paralelos simultâneos | 3 |
| Timeout por agente | 120 segundos |
| Tentativas de retry | 2 |

---

## 5. Escopo de Prompts

Cada agente possui um arquivo `.md` dedicado em `src/prompts/` com:
- Persona e especialidade
- Contexto de mercado e referências (Nielsen Norman, Google Material, AWS Well-Architected, etc.)
- Instruções de output estruturado
- Exemplos de entregáveis esperados

Total de documentação de prompts: ~3.080 linhas de markdown.

```
src/prompts/
├── design/
│   ├── brand_designer.md
│   ├── ux_designer.md
│   ├── ui_designer.md
│   └── ux_writer.md
├── engineering/
│   ├── tech_lead.md
│   ├── frontend_dev.md
│   ├── backend_dev.md
│   └── mobile_dev.md
└── quality/
    ├── qa_engineer.md
    └── devops_engineer.md
```

---

## 6. Fora do Escopo (Out of Scope)

| Item | Justificativa |
|------|--------------|
| Editor visual de prompts na UI | Prompts são arquivos `.md` editados diretamente |
| Execução de código gerado pelo sistema | O sistema gera código; não executa nem faz deploy |
| Autenticação/autorização de usuários | Sistema single-tenant sem controle de acesso |
| Integração nativa com Figma, GitHub, Jira | Integrações externas são responsabilidade do usuário |
| Suporte a outros modelos de IA além de Claude | Arquitetura acoplada ao SDK Anthropic |
| Modo offline | Requer conexão com Anthropic API e Supabase |

---

## 7. Fluxo de Execução (End-to-End)

```
1. Entrada
   ├── CLI: python main.py run <PROJECT_ID> "descrição da tarefa"
   └── Web: formulário de briefing + seleção de squad

2. Classificação
   └── task_classifier.py detecta tipo de tarefa por keywords

3. Montagem do Plano
   └── orchestrator.py seleciona agentes e define fases

4. Execução por Fases
   ├── Fase 1 (Design): brand_designer → ux_designer (paralelo dentro da fase)
   ├── Fase 2 (UX/UI): ui_designer + ux_writer (paralelo)
   ├── Fase 3 (Engenharia): tech_lead → frontend + backend + mobile (paralelo)
   └── Fase 4 (QA/DevOps): qa_engineer + devops_engineer (paralelo)

5. Passagem de Contexto
   └── Cada fase recebe outputs das fases anteriores como contexto

6. Persistência
   └── Cada execução de agente salva no Supabase (input, output, métricas)

7. Consolidação
   └── task_results agrega todos os outputs em markdown final

8. Geração de Artefatos
   └── deployer.py extrai código, cria build estática servida via Flask
```

---

## 8. Requisitos Não-Funcionais

| Requisito | Meta |
|-----------|------|
| Tempo de execução (full_product) | < 10 minutos |
| Tempo de execução (quick_ui) | < 3 minutos |
| Disponibilidade | Alta (Railway.app com auto-restart) |
| Rastreabilidade | 100% das execuções persistidas no banco |
| Escalabilidade | Horizontal via aumento de workers Gunicorn |
| Manutenibilidade | Prompts editáveis sem mudança de código |

---

## 9. Dependências Externas

| Serviço | Finalidade | Criticidade |
|---------|-----------|-------------|
| Anthropic API | Motor de IA dos agentes | Crítica (sem fallback) |
| Supabase | Persistência de dados | Alta (sistema degrada sem DB) |
| Railway.app | Hospedagem da aplicação | Alta |
| Docker Hub | Base image python:3.12-slim | Baixa (cache local) |

---

## 10. Estrutura de Entregas por Fase do Projeto

### Fase 1 — Fundação (Concluída)
- [x] Arquitetura multi-agente com BaseAgent
- [x] 10 agentes especializados com prompts detalhados
- [x] Orquestrador com execução paralela por fases
- [x] Modelos de dados com Pydantic
- [x] Integração com Supabase
- [x] CLI funcional

### Fase 2 — Interface Web (Concluída)
- [x] UI Flask com seleção de squads
- [x] Acompanhamento em tempo real
- [x] Geração de builds estáticas
- [x] PixelBridge para visualização dos agentes
- [x] Deploy em produção (Railway + Docker)

### Fase 3 — Qualidade e Robustez (Em andamento)
- [ ] Cobertura completa de testes automatizados
- [ ] Tratamento de erros e retry com backoff
- [ ] Validação de inputs do usuário
- [ ] Monitoramento e alertas em produção

### Fase 4 — Evolução (Backlog)
- [ ] Autenticação multi-usuário
- [ ] Histórico de projetos na UI
- [ ] Exportação de artefatos (PDF, ZIP)
- [ ] Templates de projetos pré-configurados
- [ ] Feedback loop: usuário avalia outputs dos agentes
- [ ] Suporte a múltiplos modelos de IA

---

## 11. Critérios de Aceite

| Funcionalidade | Critério |
|----------------|----------|
| Execução de tarefa via CLI | Completa sem erros, persiste resultado no DB |
| Execução via Web | Interface exibe progresso em tempo real e resultado final |
| Passagem de contexto | Agente de fase N usa outputs das fases 1..N-1 |
| Persistência | Toda execução consultável via `python main.py status <id>` |
| Build estática | Código extraído acessível via URL após execução |
| Plano automático | Classificador detecta tipo correto para 80%+ dos inputs |

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Timeout da API Anthropic em prompts longos | Média | Alto | Timeout configurável + retry com backoff |
| Inconsistência entre outputs de agentes | Média | Alto | Contexto compartilhado + prompts com instruções de coerência |
| Custo elevado de tokens em full_product | Alta | Médio | Planos menores disponíveis; monitoramento de tokens por execução |
| Falha no Supabase | Baixa | Alto | Tratamento de erro com logs locais como fallback |
| Qualidade variável dos outputs | Média | Alto | Prompts com exemplos e estrutura de output definida |

---

*Documento gerado em 05/04/2026 — Versão 1.0*
