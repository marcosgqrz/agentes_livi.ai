import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.orchestrator import Orchestrator
from src.database.models import (
    Task, TaskStatus, ExecutionPhase, ExecutionPlan,
    AgentExecution, AgentCategory
)


class TestOrchestrator:
    """Testes para o Orquestrador central."""

    @patch("src.orchestrator.SupabaseClient")
    def test_get_available_agents(self, mock_db):
        """Verifica que todos os 10 agentes estão registrados."""
        orchestrator = Orchestrator()
        agents = orchestrator.get_available_agents()

        assert len(agents) == 10
        expected_agents = [
            "brand_designer", "ux_designer", "ui_designer", "ux_writer",
            "frontend_dev", "mobile_dev", "backend_dev", "tech_lead",
            "qa_engineer", "devops_engineer"
        ]
        for agent_name in expected_agents:
            assert agent_name in agents
            assert isinstance(agents[agent_name], list)
            assert len(agents[agent_name]) > 0

    @patch("src.orchestrator.SupabaseClient")
    def test_get_execution_plans(self, mock_db):
        """Verifica que todos os planos de execução estão listados."""
        orchestrator = Orchestrator()
        plans = orchestrator.get_execution_plans()

        assert "full_product" in plans
        assert "mobile_app" in plans
        assert "design_only" in plans
        assert "dev_only" in plans
        assert "quick_ui" in plans

    @patch("src.orchestrator.SupabaseClient")
    def test_consolidate_outputs(self, mock_db):
        """Verifica que outputs são consolidados na ordem correta."""
        orchestrator = Orchestrator()
        outputs = {
            "brand_designer": "Brand output",
            "ux_designer": "UX output",
            "frontend_dev": "Frontend output"
        }

        result = orchestrator._consolidate_outputs(outputs)

        assert "Brand Designer" in result
        assert "Ux Designer" in result
        assert "Frontend Dev" in result
        # Brand deve vir antes de UX
        assert result.index("Brand Designer") < result.index("Ux Designer")
        # UX deve vir antes de Frontend
        assert result.index("Ux Designer") < result.index("Frontend Dev")

    @patch("src.orchestrator.SupabaseClient")
    def test_generate_summary(self, mock_db):
        """Verifica geração de sumário."""
        orchestrator = Orchestrator()
        outputs = {
            "brand_designer": "output1",
            "ux_designer": "output2"
        }

        summary = orchestrator._generate_summary(outputs)

        assert "2 agentes" in summary
        assert "brand_designer" in summary
        assert "ux_designer" in summary

    @patch("src.orchestrator.SupabaseClient")
    def test_extract_deliverables(self, mock_db):
        """Verifica extração de entregáveis."""
        orchestrator = Orchestrator()
        outputs = {
            "brand_designer": "output",
            "frontend_dev": "output"
        }

        deliverables = orchestrator._extract_deliverables(outputs)

        assert len(deliverables) == 2
        types = [d["type"] for d in deliverables]
        assert "Identidade Visual e Brandbook" in types
        assert "Código Frontend" in types
