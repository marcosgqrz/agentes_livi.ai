from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class TechLeadAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="tech_lead",
            category=AgentCategory.ENGINEERING,
            prompt_file="engineering/tech_lead.md"
        )

    def get_capabilities(self) -> list:
        return [
            "arquitetura_sistemas",
            "definicao_stack",
            "padroes_codigo",
            "modelagem_dados",
            "apis",
            "seguranca",
            "escalabilidade",
            "code_review",
            "mentoria_tecnica"
        ]

    def get_output_schema(self) -> dict:
        return {
            "arquitetura": "Diagrama e descrição da arquitetura",
            "stack": "Tecnologias escolhidas com justificativa",
            "estrutura": "Organização de código e pastas",
            "modelos": "Modelagem de dados",
            "apis": "Contratos de API",
            "seguranca": "Requisitos de segurança",
            "roadmap_tecnico": "Fases de implementação"
        }
