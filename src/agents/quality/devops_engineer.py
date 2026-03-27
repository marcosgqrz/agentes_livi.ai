from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class DevOpsEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="devops_engineer",
            category=AgentCategory.QUALITY,
            prompt_file="quality/devops_engineer.md"
        )

    def get_capabilities(self) -> list:
        return [
            "ci_cd",
            "docker",
            "kubernetes",
            "terraform",
            "aws",
            "gcp",
            "monitoramento",
            "logging",
            "seguranca_infra",
            "backup",
            "disaster_recovery"
        ]

    def get_output_schema(self) -> dict:
        return {
            "arquitetura_infra": "Diagrama de infraestrutura",
            "ci_cd": "Pipelines de CI/CD",
            "docker": "Dockerfiles e compose",
            "iac": "Infrastructure as Code",
            "monitoramento": "Setup de observabilidade",
            "runbooks": "Procedimentos operacionais"
        }
