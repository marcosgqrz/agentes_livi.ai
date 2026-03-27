from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class MobileDevAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="mobile_dev",
            category=AgentCategory.ENGINEERING,
            prompt_file="engineering/mobile_dev.md"
        )

    def get_capabilities(self) -> list:
        return [
            "react_native",
            "flutter",
            "expo",
            "ios",
            "android",
            "navegacao_mobile",
            "push_notifications",
            "deep_links",
            "offline_first",
            "app_store_deploy"
        ]

    def get_output_schema(self) -> dict:
        return {
            "arquitetura_app": "Estrutura do app mobile",
            "codigo": "Código dos componentes e telas",
            "navegacao": "Configuração de rotas",
            "integracao_api": "Cliente API configurado",
            "instrucoes": "Como rodar em simulador/device"
        }
