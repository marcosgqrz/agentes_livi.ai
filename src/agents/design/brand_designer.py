from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class BrandDesignerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="brand_designer",
            category=AgentCategory.DESIGN,
            prompt_file="design/brand_designer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "identidade_visual",
            "logotipo",
            "paleta_cores",
            "tipografia",
            "brandbook",
            "posicionamento",
            "tom_de_voz"
        ]

    def get_output_schema(self) -> dict:
        return {
            "posicionamento": "Proposta de posicionamento da marca",
            "personalidade": "Arquétipo e personalidade",
            "paleta_cores": "Cores primárias e secundárias com hex",
            "tipografia": "Fontes recomendadas",
            "tom_de_voz": "Guidelines de comunicação",
            "aplicacoes": "Exemplos de aplicação"
        }
