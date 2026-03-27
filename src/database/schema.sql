-- Habilita extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABELA: projects
-- Agrupa tarefas e mantém contexto persistente
-- ============================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    brand_context JSONB DEFAULT '{}',
    design_system JSONB DEFAULT '{}',
    tech_stack JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'completed'))
);

-- ============================================
-- TABELA: tasks
-- Tarefas submetidas ao orquestrador
-- ============================================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    input_task TEXT NOT NULL,
    execution_plan JSONB DEFAULT '[]',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- TABELA: agent_executions
-- Registro de cada execução de agente
-- ============================================
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    agent_category TEXT NOT NULL CHECK (agent_category IN ('design', 'engineering', 'quality')),
    phase_number INT NOT NULL,
    input_context JSONB DEFAULT '{}',
    output_text TEXT NOT NULL,
    output_structured JSONB DEFAULT '{}',
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    execution_time_ms INT DEFAULT 0,
    status TEXT DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABELA: task_results
-- Output consolidado final de cada tarefa
-- ============================================
CREATE TABLE task_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    final_output TEXT NOT NULL,
    summary TEXT,
    deliverables JSONB DEFAULT '[]',
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'revision_needed')),
    review_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABELA: project_context
-- Contexto persistente reutilizável entre tarefas
-- ============================================
CREATE TABLE project_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    context_type TEXT NOT NULL,
    context_key TEXT NOT NULL,
    content JSONB NOT NULL,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_task_id UUID REFERENCES tasks(id),
    UNIQUE(project_id, context_type, context_key)
);

-- ============================================
-- TABELA: execution_plans
-- Templates de planos de execução por tipo de tarefa
-- ============================================
CREATE TABLE execution_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    task_types TEXT[] NOT NULL,
    phases JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX idx_agent_executions_task ON agent_executions(task_id);
CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_name);
CREATE INDEX idx_project_context_lookup ON project_context(project_id, context_type, is_active);

-- ============================================
-- FUNÇÕES E TRIGGERS
-- ============================================

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER task_results_updated_at
    BEFORE UPDATE ON task_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER project_context_updated_at
    BEFORE UPDATE ON project_context
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- DADOS INICIAIS: Planos de Execução Padrão
-- ============================================
INSERT INTO execution_plans (name, description, task_types, phases, is_default) VALUES

('full_product', 'Fluxo completo: branding → design → dev → QA',
 ARRAY['landing_page', 'website', 'webapp', 'mvp'],
'[
  {"phase": 1, "agents": ["brand_designer"], "parallel": false},
  {"phase": 2, "agents": ["ux_designer", "ux_writer"], "parallel": true},
  {"phase": 3, "agents": ["ui_designer"], "parallel": false},
  {"phase": 4, "agents": ["tech_lead"], "parallel": false},
  {"phase": 5, "agents": ["frontend_dev", "backend_dev"], "parallel": true},
  {"phase": 6, "agents": ["qa_engineer"], "parallel": false},
  {"phase": 7, "agents": ["devops_engineer"], "parallel": false}
]'::jsonb, TRUE),

('mobile_app', 'Fluxo para aplicativo mobile',
ARRAY['mobile_app', 'ios_app', 'android_app', 'app'],
'[
  {"phase": 1, "agents": ["brand_designer"], "parallel": false},
  {"phase": 2, "agents": ["ux_designer", "ux_writer"], "parallel": true},
  {"phase": 3, "agents": ["ui_designer"], "parallel": false},
  {"phase": 4, "agents": ["tech_lead"], "parallel": false},
  {"phase": 5, "agents": ["mobile_dev", "backend_dev"], "parallel": true},
  {"phase": 6, "agents": ["qa_engineer"], "parallel": false},
  {"phase": 7, "agents": ["devops_engineer"], "parallel": false}
]'::jsonb, FALSE),

('design_only', 'Apenas design, sem desenvolvimento',
ARRAY['branding', 'identidade_visual', 'design_system', 'prototipo'],
'[
  {"phase": 1, "agents": ["brand_designer"], "parallel": false},
  {"phase": 2, "agents": ["ux_designer", "ux_writer"], "parallel": true},
  {"phase": 3, "agents": ["ui_designer"], "parallel": false}
]'::jsonb, FALSE),

('dev_only', 'Apenas desenvolvimento (design já existe)',
ARRAY['implementacao', 'codigo', 'feature', 'integracao'],
'[
  {"phase": 1, "agents": ["tech_lead"], "parallel": false},
  {"phase": 2, "agents": ["frontend_dev", "backend_dev"], "parallel": true},
  {"phase": 3, "agents": ["qa_engineer"], "parallel": false},
  {"phase": 4, "agents": ["devops_engineer"], "parallel": false}
]'::jsonb, FALSE),

('quick_ui', 'UI/UX rápido para componente específico',
ARRAY['componente', 'tela', 'modal', 'formulario'],
'[
  {"phase": 1, "agents": ["ux_designer"], "parallel": false},
  {"phase": 2, "agents": ["ui_designer", "ux_writer"], "parallel": true},
  {"phase": 3, "agents": ["frontend_dev"], "parallel": false}
]'::jsonb, FALSE);
