from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class UIDesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ui_designer",
            category=AgentCategory.DESIGN,
            prompt_file="design/ui_designer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "design_visual",
            "alta_fidelidade",
            "design_system",
            "componentes_visuais",
            "iconografia",
            "ilustracoes",
            "motion_design",
            "prototipagem",
            "handoff_dev"
        ]

    def get_output_schema(self) -> dict:
        return {
            "design_system": "Tokens e componentes do design system",
            "telas": "Especificações detalhadas de cada tela",
            "componentes": "Biblioteca de componentes com estados",
            "assets": "Lista de assets necessários",
            "specs_dev": "Especificações técnicas para desenvolvimento"
        }
