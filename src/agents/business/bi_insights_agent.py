from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class BIInsightsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="bi_insights_agent",
            category=AgentCategory.BUSINESS,
            prompt_file="business/bi_insights_agent.md"
        )

    def get_capabilities(self) -> list:
        return [
            "north_star_metric",
            "dashboard_kpis",
            "analise_funil",
            "cohort_analysis",
            "segmentacao_ltv",
            "modelagem_churn",
            "roi_marketing",
            "relatorio_impacto_social",
            "relatorio_executivo"
        ]

    def get_output_schema(self) -> dict:
        return {
            "north_star_metric": "Métrica principal e métricas de suporte",
            "dashboard_negocio": "KPIs por produto com metas e status",
            "analise_funil": "Gargalos de conversão e hipóteses",
            "segmentacao_clientes": "Matriz RFM e estratégia por segmento",
            "roi_canais": "Retorno por canal de marketing",
            "impacto_social": "Valor gerado para os usuários",
            "relatorio_executivo": "Sumário mensal para tomada de decisão"
        }
