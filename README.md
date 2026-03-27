# Agent Orchestrator — Orquestrador Multi-Agente de Produto Digital

Sistema de orquestração de múltiplos agentes de IA especializados que simulam uma equipe completa de produto digital. Utiliza a API da Anthropic (Claude) para cada agente e Supabase para persistência.

## Visão Geral

O sistema recebe uma tarefa (ex: "criar landing page para SaaS de automação") e orquestra automaticamente os agentes necessários, respeitando dependências entre eles e consolidando o output final.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMADA DE ENTRADA                        │
│                    (CLI — expansível para API/Slack)            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORQUESTRADOR CENTRAL                       │
│  - Classifica tarefa                                            │
│  - Define plano de execução (quais agentes, em qual ordem)     │
│  - Gerencia contexto compartilhado                              │
│  - Consolida outputs                                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   DESIGN &    │     │  ENGENHARIA   │     │  QUALIDADE    │
│   BRANDING    │     │               │     │  & INFRA      │
└───────────────┘     └───────────────┘     └───────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SUPABASE                                │
│     (Projetos, Tarefas, Outputs, Contexto Persistente)         │
└─────────────────────────────────────────────────────────────────┘
```

## Agentes Disponíveis

### Design & Branding
| Agente | Especialidade |
|--------|--------------|
| `brand_designer` | Identidade visual, brandbook, paleta, tipografia, tom de voz |
| `ux_designer` | Personas, wireframes, fluxos, arquitetura de informação |
| `ui_designer` | Design system, tokens, telas de alta fidelidade, handoff dev |
| `ux_writer` | Microcopy, mensagens de sistema, onboarding, textos de interface |

### Engenharia
| Agente | Especialidade |
|--------|--------------|
| `tech_lead` | Arquitetura, stack, modelagem de dados, APIs, segurança |
| `frontend_dev` | React/Next.js, TypeScript, Tailwind, componentes, acessibilidade |
| `backend_dev` | Node.js/Fastify, APIs REST, autenticação, banco de dados |
| `mobile_dev` | React Native/Expo, iOS/Android, offline-first, deploy em lojas |

### Qualidade & Infra
| Agente | Especialidade |
|--------|--------------|
| `qa_engineer` | Plano de testes, E2E (Playwright), performance (k6), bug reports |
| `devops_engineer` | CI/CD (GitHub Actions), Docker, Terraform, AWS, monitoramento |

## Planos de Execução

| Plano | Agentes | Casos de Uso |
|-------|---------|-------------|
| `full_product` | Todos os 10 | Landing page, website, webapp, MVP |
| `mobile_app` | Brand → UX/Writer → UI → TechLead → Mobile+Backend → QA → DevOps | App iOS/Android |
| `design_only` | Brand → UX/Writer → UI | Branding, design system, protótipo |
| `dev_only` | TechLead → Frontend+Backend → QA → DevOps | Implementação com design existente |
| `quick_ui` | UX → UI+Writer → Frontend | Componente, tela, modal, formulário |

## Pré-requisitos

- Python 3.10+
- Conta na [Anthropic](https://console.anthropic.com)
- Projeto no [Supabase](https://supabase.com)

## Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd agent-orchestrator

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves
```

## Configuração

### 1. Variáveis de Ambiente (`.env`)

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
LOG_LEVEL=INFO
```

### 2. Supabase

Execute o schema no SQL Editor do seu projeto Supabase:

```bash
# Copie o conteúdo de src/database/schema.sql
# e execute no SQL Editor do Supabase
```

O schema cria as tabelas:
- `projects` — Projetos e contexto persistente
- `tasks` — Tarefas submetidas ao orquestrador
- `agent_executions` — Registro de cada execução
- `task_results` — Output consolidado final
- `project_context` — Contexto reutilizável entre tarefas
- `execution_plans` — Templates de planos por tipo de tarefa

## Uso

### Listar agentes disponíveis

```bash
python main.py agents
```

### Criar um novo projeto

```bash
python main.py new-project "Meu SaaS" --description "Plataforma de automação de marketing"
```

### Listar projetos

```bash
python main.py list-projects
```

### Executar uma tarefa

```bash
python main.py run <PROJECT_ID> "Criar landing page para SaaS de automação de marketing" \
  --type full_product \
  --output resultado.md
```

### Verificar status de uma tarefa

```bash
python main.py status <TASK_ID>
```

## Exemplos de Tarefas

```bash
# Produto completo
python main.py run <ID> "Criar landing page para SaaS de CRM para pequenas empresas" -t full_product

# Apenas design
python main.py run <ID> "Criar identidade visual para fintech de investimentos" -t design_only

# App mobile
python main.py run <ID> "Criar app de delivery de comida saudável" -t mobile_app

# Apenas desenvolvimento
python main.py run <ID> "Implementar sistema de autenticação com OAuth" -t dev_only

# UI rápido
python main.py run <ID> "Criar formulário de cadastro multi-etapas" -t quick_ui
```

## Estrutura do Projeto

```
agent-orchestrator/
├── src/
│   ├── orchestrator.py           # Orquestrador central
│   ├── task_classifier.py        # Classifica tarefa e define plano
│   ├── agents/
│   │   ├── base_agent.py         # Classe base abstrata
│   │   ├── design/               # Agentes de Design & Branding
│   │   │   ├── brand_designer.py
│   │   │   ├── ux_designer.py
│   │   │   ├── ui_designer.py
│   │   │   └── ux_writer.py
│   │   ├── engineering/          # Agentes de Engenharia
│   │   │   ├── frontend_dev.py
│   │   │   ├── mobile_dev.py
│   │   │   ├── backend_dev.py
│   │   │   └── tech_lead.py
│   │   └── quality/              # Agentes de Qualidade & Infra
│   │       ├── qa_engineer.py
│   │       └── devops_engineer.py
│   ├── prompts/                  # System prompts dos agentes
│   │   ├── design/
│   │   ├── engineering/
│   │   └── quality/
│   ├── database/
│   │   ├── supabase_client.py    # Cliente Supabase
│   │   ├── models.py             # Pydantic models
│   │   └── schema.sql            # Schema do banco
│   └── utils/
│       ├── logger.py
│       └── config.py
├── tests/
├── config/
│   └── settings.py
├── .env.example
├── requirements.txt
├── main.py
└── README.md
```

## Arquitetura Técnica

### Execução Paralela

Agentes em uma mesma fase com `"parallel": true` são executados simultaneamente via `ThreadPoolExecutor`, com no máximo `max_parallel_agents` (padrão: 3) rodando ao mesmo tempo.

### Contexto Compartilhado

Cada agente recebe:
- **`context`**: Outputs de todos os agentes das fases anteriores
- **`project_context`**: Contexto persistente do projeto (brand, design system, tech stack)

Isso garante que o UI Designer, por exemplo, receba as decisões do Brand Designer e do UX Designer antes de trabalhar.

### Persistência

Todos os outputs são salvos no Supabase, permitindo:
- Retomar projetos entre sessões
- Reutilizar contexto de brand/design em novas tarefas
- Auditoria completa de tokens consumidos e tempo de execução

## Configurações Avançadas (`config/settings.py`)

```python
model: str = "claude-sonnet-4-20250514"  # Modelo usado
max_tokens: int = 4096                    # Max tokens por resposta
max_parallel_agents: int = 3             # Agentes paralelos simultâneos
default_timeout_seconds: int = 120       # Timeout por agente
retry_attempts: int = 2                  # Tentativas em caso de erro
```

## Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio

# Rodar todos os testes
pytest tests/

# Rodar teste específico
pytest tests/test_agents.py -v
```

## Licença

MIT
