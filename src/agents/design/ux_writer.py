from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class UXWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ux_writer",
            category=AgentCategory.DESIGN,
            prompt_file="design/ux_writer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "microcopy",
            "textos_interface",
            "mensagens_erro",
            "mensagens_sucesso",
            "onboarding",
            "tooltips",
            "ctas",
            "empty_states",
            "notificacoes",
            "emails_transacionais"
        ]

    def get_output_schema(self) -> dict:
        return {
            "voice_chart": "Guia de tom de voz aplicado",
            "microcopy_library": "Biblioteca de textos por componente",
            "mensagens_sistema": "Erros, sucessos, alertas",
            "fluxos_texto": "Textos de onboarding e jornadas",
            "glossario": "Termos padronizados do produto"
        }
