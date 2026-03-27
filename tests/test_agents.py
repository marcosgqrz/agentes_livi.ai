import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from src.agents.design.brand_designer import BrandDesignerAgent
from src.agents.design.ux_designer import UXDesignerAgent
from src.agents.design.ui_designer import UIDesignerAgent
from src.agents.design.ux_writer import UXWriterAgent
from src.agents.engineering.frontend_dev import FrontendDevAgent
from src.agents.engineering.mobile_dev import MobileDevAgent
from src.agents.engineering.backend_dev import BackendDevAgent
from src.agents.engineering.tech_lead import TechLeadAgent
from src.agents.quality.qa_engineer import QAEngineerAgent
from src.agents.quality.devops_engineer import DevOpsEngineerAgent
from src.database.models import AgentCategory


class TestAgentCreation:
    """Testa que todos os agentes podem ser instanciados."""

    def test_brand_designer(self):
        agent = BrandDesignerAgent()
        assert agent.name == "brand_designer"
        assert agent.category == AgentCategory.DESIGN
        assert len(agent.get_capabilities()) > 0
        assert len(agent.get_output_schema()) > 0

    def test_ux_designer(self):
        agent = UXDesignerAgent()
        assert agent.name == "ux_designer"
        assert agent.category == AgentCategory.DESIGN

    def test_ui_designer(self):
        agent = UIDesignerAgent()
        assert agent.name == "ui_designer"
        assert agent.category == AgentCategory.DESIGN

    def test_ux_writer(self):
        agent = UXWriterAgent()
        assert agent.name == "ux_writer"
        assert agent.category == AgentCategory.DESIGN

    def test_frontend_dev(self):
        agent = FrontendDevAgent()
        assert agent.name == "frontend_dev"
        assert agent.category == AgentCategory.ENGINEERING

    def test_mobile_dev(self):
        agent = MobileDevAgent()
        assert agent.name == "mobile_dev"
        assert agent.category == AgentCategory.ENGINEERING

    def test_backend_dev(self):
        agent = BackendDevAgent()
        assert agent.name == "backend_dev"
        assert agent.category == AgentCategory.ENGINEERING

    def test_tech_lead(self):
        agent = TechLeadAgent()
        assert agent.name == "tech_lead"
        assert agent.category == AgentCategory.ENGINEERING

    def test_qa_engineer(self):
        agent = QAEngineerAgent()
        assert agent.name == "qa_engineer"
        assert agent.category == AgentCategory.QUALITY

    def test_devops_engineer(self):
        agent = DevOpsEngineerAgent()
        assert agent.name == "devops_engineer"
        assert agent.category == AgentCategory.QUALITY


class TestAgentPrompts:
    """Testa que todos os prompts existem e são carregados."""

    def test_all_agents_have_prompts(self):
        agents = [
            BrandDesignerAgent, UXDesignerAgent, UIDesignerAgent, UXWriterAgent,
            FrontendDevAgent, MobileDevAgent, BackendDevAgent, TechLeadAgent,
            QAEngineerAgent, DevOpsEngineerAgent
        ]
        for AgentClass in agents:
            agent = AgentClass()
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 100, f"{agent.name} prompt is too short"


class TestAgentExecution:
    """Testa a execução de agentes com mock da API."""

    @patch("src.agents.base_agent.Anthropic")
    def test_agent_execute_success(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test output")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 200
        mock_client.messages.create.return_value = mock_response

        agent = BrandDesignerAgent()
        agent.client = mock_client

        result = agent.execute(
            task="Test task",
            task_id=uuid4(),
            phase_number=1
        )

        assert result.status == "completed"
        assert result.output_text == "Test output"
        assert result.tokens_input == 100
        assert result.tokens_output == 200

    @patch("src.agents.base_agent.Anthropic")
    def test_agent_execute_failure(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        agent = BrandDesignerAgent()
        agent.client = mock_client

        result = agent.execute(
            task="Test task",
            task_id=uuid4(),
            phase_number=1
        )

        assert result.status == "failed"
        assert "API Error" in result.error_message
