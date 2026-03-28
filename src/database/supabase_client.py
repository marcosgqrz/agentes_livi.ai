from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from config.settings import settings
from .models import (
    Project, Task, TaskStatus, AgentExecution,
    TaskResult, ExecutionPlan, ExecutionPhase
)


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

        return None

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
