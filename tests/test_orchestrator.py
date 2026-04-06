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

    @patch("src.orchestrator.create_db_client")
    def test_get_available_agents(self, mock_db):
        """Verifica que todos os 16 agentes estão registrados."""
        orchestrator = Orchestrator(db=MagicMock())
        agents = orchestrator.get_available_agents()

        assert len(agents) == 16
        expected_agents = [
            # Design
            "brand_designer", "ux_designer", "ui_designer", "ux_writer",
            # Engineering
            "frontend_dev", "mobile_dev", "backend_dev", "tech_lead",
            # Quality
            "qa_engineer", "devops_engineer",
            # Growth
            "traffic_manager", "seo_specialist", "social_media_strategist",
            # Business
            "sales_representative", "customer_success", "bi_insights_agent",
        ]
        for agent_name in expected_agents:
            assert agent_name in agents
            assert isinstance(agents[agent_name], list)
            assert len(agents[agent_name]) > 0

    @patch("src.orchestrator.create_db_client")
    def test_get_execution_plans(self, mock_db):
        """Verifica que todos os planos de execução estão listados."""
        orchestrator = Orchestrator(db=MagicMock())
        plans = orchestrator.get_execution_plans()

        assert "full_product" in plans
        assert "mobile_app" in plans
        assert "design_only" in plans
        assert "dev_only" in plans
        assert "quick_ui" in plans
        assert "growth_only" in plans
        assert "business_only" in plans
        assert "full_go_to_market" in plans

    @patch("src.orchestrator.create_db_client")
    def test_consolidate_outputs(self, mock_db):
        """Verifica que outputs são consolidados na ordem correta."""
        orchestrator = Orchestrator(db=MagicMock())
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

    @patch("src.orchestrator.create_db_client")
    def test_generate_summary(self, mock_db):
        """Verifica geração de sumário."""
        orchestrator = Orchestrator(db=MagicMock())
        outputs = {
            "brand_designer": "output1",
            "ux_designer": "output2"
        }

        summary = orchestrator._generate_summary(outputs)

        assert "2 agentes" in summary
        assert "brand_designer" in summary
        assert "ux_designer" in summary

    @patch("src.orchestrator.create_db_client")
    def test_extract_deliverables(self, mock_db):
        """Verifica extração de entregáveis."""
        orchestrator = Orchestrator(db=MagicMock())
        outputs = {
            "brand_designer": "output",
            "frontend_dev": "output"
        }

        deliverables = orchestrator._extract_deliverables(outputs)

        assert len(deliverables) == 2
        types = [d["type"] for d in deliverables]
        assert "Identidade Visual e Brandbook" in types
        assert "Código Frontend" in types

    @patch("src.orchestrator.create_db_client")
    def test_build_squad_plan(self, mock_db):
        """Verifica criação dinâmica de plano para squads."""
        orchestrator = Orchestrator(db=MagicMock())

        # Squad de Criação
        plan = orchestrator._build_squad_plan("criacao", ["brand_designer", "ux_designer", "ui_designer", "ux_writer"])
        agents_in_plan = [a for phase in plan.phases for a in phase.agents]
        assert "brand_designer" in agents_in_plan
        assert "ux_designer" in agents_in_plan
        assert "ui_designer" in agents_in_plan
        assert "ux_writer" in agents_in_plan

        # Squad de Crescimento
        plan = orchestrator._build_squad_plan("crescimento", ["traffic_manager", "seo_specialist", "social_media_strategist"])
        agents_in_plan = [a for phase in plan.phases for a in phase.agents]
        assert "traffic_manager" in agents_in_plan
        assert "seo_specialist" in agents_in_plan
        assert "social_media_strategist" in agents_in_plan
