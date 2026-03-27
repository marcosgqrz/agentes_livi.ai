from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class QAEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="qa_engineer",
            category=AgentCategory.QUALITY,
            prompt_file="quality/qa_engineer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "plano_testes",
            "casos_teste",
            "testes_automatizados",
            "testes_e2e",
            "testes_unitarios",
            "testes_integracao",
            "testes_performance",
            "testes_seguranca",
            "bug_reporting",
            "regressao"
        ]

    def get_output_schema(self) -> dict:
        return {
            "plano_testes": "Estratégia de testes",
            "casos_teste": "Lista de casos de teste",
            "scripts_automacao": "Código de testes automatizados",
            "checklist_qa": "Checklist de validação",
            "metricas": "Métricas de qualidade"
        }
