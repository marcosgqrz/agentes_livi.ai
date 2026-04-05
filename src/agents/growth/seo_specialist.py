from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class SEOSpecialistAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="seo_specialist",
            category=AgentCategory.GROWTH,
            prompt_file="growth/seo_specialist.md"
        )

    def get_capabilities(self) -> list:
        return [
            "pesquisa_palavras_chave",
            "topic_clusters",
            "otimizacao_on_page",
            "seo_tecnico",
            "core_web_vitals",
            "link_building",
            "auditoria_seo",
            "projecao_organica"
        ]

    def get_output_schema(self) -> dict:
        return {
            "mapa_keywords": "Clusters de palavras-chave por intenção",
            "arquitetura_conteudo": "Estrutura de pillar pages e clusters",
            "checklist_tecnico": "Auditoria técnica de SEO",
            "estrategia_link_building": "Fontes e templates de outreach",
            "projecao_crescimento": "Tráfego orgânico projetado por mês"
        }
