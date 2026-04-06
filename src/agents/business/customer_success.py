from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class CustomerSuccessAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="customer_success",
            category=AgentCategory.BUSINESS,
            prompt_file="business/customer_success.md"
        )

    def get_capabilities(self) -> list:
        return [
            "atendimento_nivel1",
            "base_conhecimento",
            "retencao_proativa",
            "deteccao_churn",
            "feedback_loop",
            "onboarding",
            "tom_de_voz_suporte",
            "relatorio_produto"
        ]

    def get_output_schema(self) -> dict:
        return {
            "base_conhecimento": "Artigos de suporte em linguagem simples",
            "fluxos_retencao": "Gatilhos e mensagens por sinal de risco",
            "manual_tom_voz": "Guia de comunicação para atendimento",
            "relatorio_semanal": "Template de feedback loop para produto",
            "checklists": "Checklist de encerramento de chamados"
        }
