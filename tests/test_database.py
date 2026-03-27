import pytest
from uuid import uuid4

from src.database.models import (
    Project, Task, TaskStatus, AgentExecution,
    TaskResult, ExecutionPhase, ExecutionPlan,
    AgentCategory, ReviewStatus
)


class TestModels:
    """Testa os modelos Pydantic."""

    def test_project_creation(self):
        project = Project(name="Test Project", description="A test")
        assert project.name == "Test Project"
        assert project.status == "active"
        assert project.brand_context == {}

    def test_task_creation(self):
        task = Task(
            project_id=uuid4(),
            task_type="landing_page",
            input_task="Create a landing page"
        )
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5

    def test_task_priority_validation(self):
        with pytest.raises(ValueError):
            Task(
                project_id=uuid4(),
                task_type="test",
                input_task="test",
                priority=11
            )

    def test_agent_execution(self):
        execution = AgentExecution(
            task_id=uuid4(),
            agent_name="brand_designer",
            agent_category=AgentCategory.DESIGN,
            phase_number=1,
            output_text="Test output"
        )
        assert execution.status == "completed"
        assert execution.tokens_input == 0

    def test_task_result(self):
        result = TaskResult(
            task_id=uuid4(),
            final_output="Final output"
        )
        assert result.review_status == ReviewStatus.PENDING
        assert result.deliverables == []

    def test_execution_phase(self):
        phase = ExecutionPhase(
            phase=1,
            agents=["brand_designer"]
        )
        assert phase.parallel is False

    def test_execution_plan(self):
        plan = ExecutionPlan(
            name="test_plan",
            task_types=["landing_page"],
            phases=[
                ExecutionPhase(phase=1, agents=["brand_designer"]),
                ExecutionPhase(phase=2, agents=["ux_designer", "ux_writer"], parallel=True)
            ]
        )
        assert len(plan.phases) == 2
        assert plan.phases[1].parallel is True
