from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class SalesRepresentativeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="sales_representative",
            category=AgentCategory.BUSINESS,
            prompt_file="business/sales_representative.md"
        )

    def get_capabilities(self) -> list:
        return [
            "prospeccao_b2b",
            "qualificacao_leads",
            "sequencias_outreach",
            "vendas_consultivas",
            "gestao_objecoes",
            "parcerias_estrategicas",
            "pipeline_comercial",
            "script_discovery"
        ]

    def get_output_schema(self) -> dict:
        return {
            "icp_definicao": "Perfil ideal de cliente com critérios de qualificação",
            "lista_prospeccao": "Empresas segmentadas por prioridade",
            "sequencias_outreach": "Cadências email + LinkedIn + telefone",
            "script_discovery": "Roteiro de call de qualificação",
            "manual_objecoes": "Respostas para objeções comuns",
            "estrutura_parceria": "Modelos de parceria e proposta template"
        }
