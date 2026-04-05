from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from config.settings import settings
from .models import (
    Project, Task, TaskStatus, AgentExecution,
    TaskResult, ExecutionPlan, ExecutionPhase
)

# ── Planos de execução embutidos (usados no modo dev sem Supabase) ─────────────
_BUILTIN_PLANS: Dict[str, ExecutionPlan] = {
    "full_product": ExecutionPlan(
        name="full_product", task_types=["full_product"],
        description="Produto completo — todos os agentes",
        phases=[
            ExecutionPhase(phase=1, agents=["brand_designer"], parallel=False),
            ExecutionPhase(phase=2, agents=["ux_designer", "ux_writer"], parallel=True),
            ExecutionPhase(phase=3, agents=["ui_designer"], parallel=False),
            ExecutionPhase(phase=4, agents=["tech_lead"], parallel=False),
            ExecutionPhase(phase=5, agents=["frontend_dev", "backend_dev"], parallel=True),
            ExecutionPhase(phase=6, agents=["qa_engineer"], parallel=False),
            ExecutionPhase(phase=7, agents=["devops_engineer"], parallel=False),
        ]
    ),
    "design_only": ExecutionPlan(
        name="design_only", task_types=["design_only"],
        description="Apenas design e identidade",
        phases=[
            ExecutionPhase(phase=1, agents=["brand_designer"], parallel=False),
            ExecutionPhase(phase=2, agents=["ux_designer", "ux_writer"], parallel=True),
            ExecutionPhase(phase=3, agents=["ui_designer"], parallel=False),
        ]
    ),
    "dev_only": ExecutionPlan(
        name="dev_only", task_types=["dev_only"],
        description="Apenas engenharia",
        phases=[
            ExecutionPhase(phase=1, agents=["tech_lead"], parallel=False),
            ExecutionPhase(phase=2, agents=["frontend_dev", "backend_dev"], parallel=True),
            ExecutionPhase(phase=3, agents=["qa_engineer"], parallel=False),
            ExecutionPhase(phase=4, agents=["devops_engineer"], parallel=False),
        ]
    ),
    "quick_ui": ExecutionPlan(
        name="quick_ui", task_types=["quick_ui"],
        description="UI rápida para validação",
        phases=[
            ExecutionPhase(phase=1, agents=["ux_designer"], parallel=False),
            ExecutionPhase(phase=2, agents=["ui_designer"], parallel=False),
            ExecutionPhase(phase=3, agents=["frontend_dev"], parallel=False),
        ]
    ),
    "mobile_app": ExecutionPlan(
        name="mobile_app", task_types=["mobile_app"],
        description="App mobile completo",
        phases=[
            ExecutionPhase(phase=1, agents=["brand_designer"], parallel=False),
            ExecutionPhase(phase=2, agents=["ux_designer", "ux_writer"], parallel=True),
            ExecutionPhase(phase=3, agents=["ui_designer"], parallel=False),
            ExecutionPhase(phase=4, agents=["tech_lead"], parallel=False),
            ExecutionPhase(phase=5, agents=["mobile_dev"], parallel=False),
            ExecutionPhase(phase=6, agents=["qa_engineer"], parallel=False),
        ]
    ),
    "growth_only": ExecutionPlan(
        name="growth_only", task_types=["growth_only"],
        description="Estratégia de crescimento e marketing",
        phases=[
            ExecutionPhase(phase=1, agents=["traffic_manager", "seo_specialist"], parallel=True),
            ExecutionPhase(phase=2, agents=["social_media_strategist"], parallel=False),
        ]
    ),
    "business_only": ExecutionPlan(
        name="business_only", task_types=["business_only"],
        description="Operações de negócio",
        phases=[
            ExecutionPhase(phase=1, agents=["sales_representative", "customer_success"], parallel=True),
            ExecutionPhase(phase=2, agents=["bi_insights_agent"], parallel=False),
        ]
    ),
    "full_go_to_market": ExecutionPlan(
        name="full_go_to_market", task_types=["full_go_to_market"],
        description="Produto + crescimento + negócio",
        phases=[
            ExecutionPhase(phase=1, agents=["brand_designer"], parallel=False),
            ExecutionPhase(phase=2, agents=["ux_designer", "ux_writer"], parallel=True),
            ExecutionPhase(phase=3, agents=["ui_designer"], parallel=False),
            ExecutionPhase(phase=4, agents=["tech_lead"], parallel=False),
            ExecutionPhase(phase=5, agents=["frontend_dev", "backend_dev"], parallel=True),
            ExecutionPhase(phase=6, agents=["qa_engineer", "devops_engineer"], parallel=True),
            ExecutionPhase(phase=7, agents=["traffic_manager", "seo_specialist", "social_media_strategist"], parallel=True),
            ExecutionPhase(phase=8, agents=["sales_representative", "customer_success"], parallel=True),
            ExecutionPhase(phase=9, agents=["bi_insights_agent"], parallel=False),
        ]
    ),
}


class InMemoryClient:
    """Substituto em memória do SupabaseClient para uso sem credenciais (modo dev)."""

    def __init__(self):
        self._projects: Dict[str, dict] = {}
        self._tasks: Dict[str, dict] = {}
        self._executions: List[dict] = []
        self._results: Dict[str, dict] = {}
        self._contexts: Dict[str, List[dict]] = {}

    # ── Projects ──────────────────────────────────────────────────────────────

    def create_project(self, name: str, description: str = "") -> Project:
        p = Project(name=name, description=description, created_at=datetime.now(), updated_at=datetime.now())
        self._projects[str(p.id)] = p.model_dump()
        return p

    def get_project(self, project_id: UUID) -> Optional[Project]:
        d = self._projects.get(str(project_id))
        return Project(**d) if d else None

    def list_projects(self, status: str = "active") -> List[Project]:
        return [Project(**d) for d in self._projects.values() if d.get("status") == status]

    def update_project_context(self, project_id: UUID, context_type: str, content: Dict[str, Any]):
        if str(project_id) in self._projects:
            field_map = {"brand": "brand_context", "design": "design_system", "tech": "tech_stack"}
            field = field_map.get(context_type)
            if field:
                self._projects[str(project_id)][field] = content

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def create_task(self, project_id: UUID, task_type: str, input_task: str, execution_plan: List[Dict] = None) -> Task:
        t = Task(
            project_id=project_id,
            task_type=task_type,
            input_task=input_task,
            execution_plan=execution_plan or [],
            created_at=datetime.now()
        )
        self._tasks[str(t.id)] = t.model_dump()
        return t

    def get_task(self, task_id: UUID) -> Optional[Task]:
        d = self._tasks.get(str(task_id))
        return Task(**d) if d else None

    def update_task_status(self, task_id: UUID, status: TaskStatus, error_message: str = None):
        d = self._tasks.get(str(task_id))
        if d:
            d["status"] = status
            if status == TaskStatus.RUNNING:
                d["started_at"] = datetime.now()
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                d["completed_at"] = datetime.now()
            if error_message:
                d["error_message"] = error_message

    def list_project_tasks(self, project_id: UUID, limit: int = 20) -> List[Task]:
        tasks = [Task(**d) for d in self._tasks.values() if str(d.get("project_id")) == str(project_id)]
        return sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=True)[:limit]

    # ── Agent Executions ──────────────────────────────────────────────────────

    def save_agent_execution(self, execution: AgentExecution) -> AgentExecution:
        self._executions.append(execution.model_dump())
        return execution

    def get_task_executions(self, task_id: UUID) -> List[AgentExecution]:
        return [AgentExecution(**e) for e in self._executions if str(e.get("task_id")) == str(task_id)]

    def get_phase_outputs(self, task_id: UUID, phase_number: int) -> Dict[str, str]:
        return {
            e["agent_name"]: e["output_text"]
            for e in self._executions
            if str(e.get("task_id")) == str(task_id) and e.get("phase_number", 0) < phase_number
        }

    # ── Task Results ──────────────────────────────────────────────────────────

    def save_task_result(self, result_data: TaskResult) -> TaskResult:
        self._results[str(result_data.task_id)] = result_data.model_dump()
        return result_data

    def get_task_result(self, task_id: UUID) -> Optional[TaskResult]:
        d = self._results.get(str(task_id))
        return TaskResult(**d) if d else None

    # ── Execution Plans ───────────────────────────────────────────────────────

    def get_execution_plan(self, task_type: str) -> Optional[ExecutionPlan]:
        return _BUILTIN_PLANS.get(task_type) or _BUILTIN_PLANS.get("full_product")

    # ── Project Context ───────────────────────────────────────────────────────

    def save_context(self, project_id: UUID, context_type: str, context_key: str, content: Dict[str, Any], task_id: UUID = None):
        key = str(project_id)
        if key not in self._contexts:
            self._contexts[key] = []
        self._contexts[key].append({
            "context_type": context_type,
            "context_key": context_key,
            "content": content
        })

    def get_project_contexts(self, project_id: UUID, context_type: str = None) -> Dict[str, Any]:
        items = self._contexts.get(str(project_id), [])
        contexts: Dict[str, Any] = {}
        for item in items:
            if context_type and item["context_type"] != context_type:
                continue
            ct = item["context_type"]
            if ct not in contexts:
                contexts[ct] = {}
            contexts[ct][item["context_key"]] = item["content"]
        return contexts


class SupabaseClient:
    def __init__(self):
        if not settings.validate():
            raise ValueError("Configurações inválidas. Verifique ANTHROPIC_API_KEY, SUPABASE_URL e SUPABASE_KEY.")

        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

    # ==================== PROJECTS ====================

    def create_project(self, name: str, description: str = "") -> Project:
        data = {"name": name, "description": description}
        result = self.client.table("projects").insert(data).execute()
        return Project(**result.data[0])

    def get_project(self, project_id: UUID) -> Optional[Project]:
        result = self.client.table("projects").select("*").eq("id", str(project_id)).execute()
        return Project(**result.data[0]) if result.data else None

    def list_projects(self, status: str = "active") -> List[Project]:
        result = self.client.table("projects").select("*").eq("status", status).order("created_at", desc=True).execute()
        return [Project(**p) for p in result.data]

    def update_project_context(self, project_id: UUID, context_type: str, content: Dict[str, Any]):
        field_map = {
            "brand": "brand_context",
            "design": "design_system",
            "tech": "tech_stack"
        }
        field = field_map.get(context_type)
        if field:
            self.client.table("projects").update({field: content}).eq("id", str(project_id)).execute()

    # ==================== TASKS ====================

    def create_task(self, project_id: UUID, task_type: str, input_task: str, execution_plan: List[Dict] = None) -> Task:
        data = {
            "project_id": str(project_id),
            "task_type": task_type,
            "input_task": input_task,
            "execution_plan": execution_plan or []
        }
        result = self.client.table("tasks").insert(data).execute()
        return Task(**result.data[0])

    def get_task(self, task_id: UUID) -> Optional[Task]:
        result = self.client.table("tasks").select("*").eq("id", str(task_id)).execute()
        return Task(**result.data[0]) if result.data else None

    def update_task_status(self, task_id: UUID, status: TaskStatus, error_message: str = None):
        update_data = {"status": status.value}

        if status == TaskStatus.RUNNING:
            update_data["started_at"] = datetime.now().isoformat()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            update_data["completed_at"] = datetime.now().isoformat()

        if error_message:
            update_data["error_message"] = error_message

        self.client.table("tasks").update(update_data).eq("id", str(task_id)).execute()

    def list_project_tasks(self, project_id: UUID, limit: int = 20) -> List[Task]:
        result = self.client.table("tasks")\
            .select("*")\
            .eq("project_id", str(project_id))\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return [Task(**t) for t in result.data]

    # ==================== AGENT EXECUTIONS ====================

    def save_agent_execution(self, execution: AgentExecution) -> AgentExecution:
        data = {
            "task_id": str(execution.task_id),
            "agent_name": execution.agent_name,
            "agent_category": execution.agent_category.value,
            "phase_number": execution.phase_number,
            "input_context": execution.input_context,
            "output_text": execution.output_text,
            "output_structured": execution.output_structured,
            "tokens_input": execution.tokens_input,
            "tokens_output": execution.tokens_output,
            "execution_time_ms": execution.execution_time_ms,
            "status": execution.status,
            "error_message": execution.error_message
        }
        result = self.client.table("agent_executions").insert(data).execute()
        return AgentExecution(**result.data[0])

    def get_task_executions(self, task_id: UUID) -> List[AgentExecution]:
        result = self.client.table("agent_executions")\
            .select("*")\
            .eq("task_id", str(task_id))\
            .order("phase_number")\
            .order("created_at")\
            .execute()
        return [AgentExecution(**e) for e in result.data]

    def get_phase_outputs(self, task_id: UUID, phase_number: int) -> Dict[str, str]:
        result = self.client.table("agent_executions")\
            .select("agent_name, output_text")\
            .eq("task_id", str(task_id))\
            .lt("phase_number", phase_number)\
            .execute()
        return {e["agent_name"]: e["output_text"] for e in result.data}

    # ==================== TASK RESULTS ====================

    def save_task_result(self, result_data: TaskResult) -> TaskResult:
        data = {
            "task_id": str(result_data.task_id),
            "final_output": result_data.final_output,
            "summary": result_data.summary,
            "deliverables": result_data.deliverables,
            "review_status": result_data.review_status.value
        }
        result = self.client.table("task_results").insert(data).execute()
        return TaskResult(**result.data[0])

    def get_task_result(self, task_id: UUID) -> Optional[TaskResult]:
        result = self.client.table("task_results").select("*").eq("task_id", str(task_id)).execute()
        return TaskResult(**result.data[0]) if result.data else None

    # ==================== EXECUTION PLANS ====================

    def get_execution_plan(self, task_type: str) -> Optional[ExecutionPlan]:
        # Busca primeiro por nome exato do plano
        result = self.client.table("execution_plans")\
            .select("*")\
            .eq("name", task_type)\
            .execute()

        if not result.data:
            # Fallback: busca por task_types que contenham o valor
            result = self.client.table("execution_plans")\
                .select("*")\
                .contains("task_types", [task_type])\
                .execute()

        if not result.data:
            # Fallback final: plano default
            result = self.client.table("execution_plans")\
                .select("*")\
                .eq("is_default", True)\
                .execute()

        if result.data:
            plan_data = result.data[0]
            plan_data["phases"] = [ExecutionPhase(**p) for p in plan_data["phases"]]
            return ExecutionPlan(**plan_data)

        return _BUILTIN_PLANS.get(task_type) or _BUILTIN_PLANS.get("full_product")

    # ==================== PROJECT CONTEXT ====================

    def save_context(self, project_id: UUID, context_type: str, context_key: str, content: Dict[str, Any], task_id: UUID = None):
        data = {
            "project_id": str(project_id),
            "context_type": context_type,
            "context_key": context_key,
            "content": content,
            "created_by_task_id": str(task_id) if task_id else None
        }

        # Upsert
        self.client.table("project_context").upsert(
            data,
            on_conflict="project_id,context_type,context_key"
        ).execute()

    def get_project_contexts(self, project_id: UUID, context_type: str = None) -> Dict[str, Any]:
        query = self.client.table("project_context")\
            .select("context_type, context_key, content")\
            .eq("project_id", str(project_id))\
            .eq("is_active", True)

        if context_type:
            query = query.eq("context_type", context_type)

        result = query.execute()

        contexts = {}
        for item in result.data:
            ctx_type = item["context_type"]
            if ctx_type not in contexts:
                contexts[ctx_type] = {}
            contexts[ctx_type][item["context_key"]] = item["content"]

        return contexts


def create_db_client():
    """
    Retorna o cliente de banco adequado:
    - SupabaseClient  → quando SUPABASE_URL + SUPABASE_KEY estão presentes
    - InMemoryClient  → modo dev, sem credenciais de banco (dados não persistem entre reinicios)
    """
    if settings.supabase_url and settings.supabase_key:
        try:
            return SupabaseClient()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Supabase indisponível ({e}). Usando armazenamento em memória (modo dev)."
            )
    import logging
    logging.getLogger(__name__).warning(
        "SUPABASE_URL/SUPABASE_KEY ausentes. Iniciando em modo dev (armazenamento em memória)."
    )
    return InMemoryClient()
