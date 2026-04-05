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
            "estrategia_instagram",
            "estrategia_tiktok",
            "gestao_engajamento",
            "influenciadores",
            "gestao_crise",
            "conteudo_humanizado"
        ]

    def get_output_schema(self) -> dict:
        return {
            "estrategia_plataformas": "Objetivo e frequência por canal",
            "calendario_editorial": "Planejamento mensal de conteúdo",
            "roteiros_reels": "Scripts prontos para vídeos curtos",
            "guia_engajamento": "Tom de resposta e comunidades",
            "perfil_influenciadores": "Critérios e briefing de parceria",
            "metricas": "KPIs de crescimento orgânico"
        }
