from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class SocialMediaStrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="social_media_strategist",
            category=AgentCategory.GROWTH,
            prompt_file="growth/social_media_strategist.md"
        )

    def get_capabilities(self) -> list:
        return [
            "calendario_editorial",
            "roteiros_reels",
            "carrosséis",
            "stories",
            "publicacao_automatica",
            "moderacao_comentarios",
            "humanizacao_marca",
            "traducao_tecniques",
            "daily_scan_tendencias",
            "content_sync_engenharia",
            "audit_glossario_proibido",
            "shadow_approval",
            "memory_update_vetorial",
            "relatorio_performance_mensal",
            "handoff_traffic_manager",
            "handoff_bi_insights"
        ]

    def get_output_schema(self) -> dict:
        return {
            "briefing_post": "Plataforma, formato, data, categoria e objetivo",
            "conteudo_completo": "Roteiro/visual + legenda completa + áudio sugerido",
            "audit_result": "Resultado do Audit & Post com status de publicação",
            "memory_update": "JSON estruturado para armazenamento vetorial",
            "relatorio_mensal": "Top posts, formato vencedor e sugestões de ajuste",
            "handoff_traffic": "Posts com score > 70 para impulsionamento pago",
            "handoff_bi": "Métricas consolidadas para o BI Insights Agent"
        }
