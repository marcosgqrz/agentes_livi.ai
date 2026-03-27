from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class UXDesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ux_designer",
            category=AgentCategory.DESIGN,
            prompt_file="design/ux_designer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "pesquisa_usuario",
            "personas",
            "jornada_usuario",
            "wireframes",
            "fluxos",
            "arquitetura_informacao",
            "usabilidade",
            "acessibilidade"
        ]

    def get_output_schema(self) -> dict:
        return {
            "personas": "Personas principais do produto",
            "jornada": "Mapa da jornada do usuário",
            "arquitetura": "Estrutura de navegação",
            "wireframes": "Descrição dos wireframes de telas principais",
            "fluxos": "Fluxos de interação críticos"
        }
