from src.agents.base_agent import BaseAgent
from src.database.models import AgentCategory


class TrafficManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="traffic_manager",
            category=AgentCategory.GROWTH,
            prompt_file="growth/traffic_manager.md"
        )

    def get_capabilities(self) -> list:
        return [
            "google_ads",
            "meta_ads",
            "trafego_pago",
            "funil_aquisicao",
            "cpa_otimizacao",
            "atribuicao",
            "testes_ab",
            "roi_canais"
        ]

    def get_output_schema(self) -> dict:
        return {
            "estrategia_canais": "Mix de investimento entre canais pagos",
            "estrutura_campanhas": "Campanhas TOFU/MOFU/BOFU com segmentações",
            "kpis_metas": "Metas de CAC, ROAS e conversão por canal",
            "plano_testes": "Hipóteses e estrutura de testes A/B",
            "modelo_atribuicao": "Modelo de atribuição recomendado",
            "relatorio_atribuicao": "Origem dos melhores clientes"
        }
