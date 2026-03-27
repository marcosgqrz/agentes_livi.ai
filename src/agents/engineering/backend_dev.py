from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class BackendDevAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="backend_dev",
            category=AgentCategory.ENGINEERING,
            prompt_file="engineering/backend_dev.md"
        )

    def get_capabilities(self) -> list:
        return [
            "nodejs",
            "python",
            "apis_rest",
            "graphql",
            "banco_dados",
            "autenticacao",
            "integracoes",
            "filas",
            "cache",
            "testes_backend"
        ]

    def get_output_schema(self) -> dict:
        return {
            "codigo": "Código completo dos módulos",
            "migrations": "Scripts de migração de banco",
            "testes": "Testes unitários e integração",
            "documentacao": "Docs de API",
            "instrucoes": "Como rodar e testar"
        }
