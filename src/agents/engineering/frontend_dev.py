from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class FrontendDevAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="frontend_dev",
            category=AgentCategory.ENGINEERING,
            prompt_file="engineering/frontend_dev.md"
        )

    def get_capabilities(self) -> list:
        return [
            "react",
            "nextjs",
            "typescript",
            "tailwindcss",
            "componentes",
            "responsividade",
            "performance",
            "acessibilidade_codigo"
        ]

    def get_output_schema(self) -> dict:
        return {
            "arquitetura": "Estrutura de pastas e componentes",
            "componentes": "Lista de componentes a criar",
            "codigo": "Código dos componentes principais",
            "dependencias": "Libs necessárias",
            "instrucoes": "Como rodar e testar"
        }
