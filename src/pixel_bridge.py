"""
pixel_bridge.py — Integração com pixel-agents-standalone

Em produção, faz chamadas HTTP para a API REST do pixel-agents-standalone
(variável de ambiente PIXEL_AGENTS_URL). Em desenvolvimento local,
aponta para http://localhost:3456 por padrão.

Endpoints usados:
  POST /api/agent/start       { agentName }  → cria agente, anima "typing"
  POST /api/agent/finish      { agentName }  → muda para "waiting"
  POST /api/agent/finish-all  {}             → fecha todos os agentes
"""

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

PIXEL_AGENTS_URL = os.environ.get("PIXEL_AGENTS_URL", "http://localhost:3456").rstrip("/")


class PixelAgentsBridge:
    """
    Gerencia animações de agentes no Pixel Office via HTTP.

    Uso no orchestrator:
        bridge = PixelAgentsBridge()
        bridge.agent_started("brand_designer")   # antes de agent.execute()
        bridge.agent_finished("brand_designer")  # depois de agent.execute()
    """

    def __init__(self):
        self._agent_ids: dict[str, int] = {}
        self._enabled = self._check_pixel_agents()

    def _check_pixel_agents(self) -> bool:
        try:
            urllib.request.urlopen(f"{PIXEL_AGENTS_URL}/", timeout=2)
            logger.info(f"[PixelBridge] pixel-agents detectado em {PIXEL_AGENTS_URL} ✓")
            return True
        except Exception:
            logger.info(f"[PixelBridge] pixel-agents não encontrado em {PIXEL_AGENTS_URL} — bridge desativada")
            return False

    def _post(self, path: str, data: dict) -> dict | None:
        try:
            body = json.dumps(data).encode()
            req = urllib.request.Request(
                f"{PIXEL_AGENTS_URL}{path}",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read())
        except Exception as e:
            logger.warning(f"[PixelBridge] HTTP POST {path} falhou: {e}")
            return None

    def agent_started(self, agent_name: str) -> None:
        if not self._enabled:
            return
        result = self._post("/api/agent/start", {"agentName": agent_name})
        if result and result.get("ok"):
            self._agent_ids[agent_name] = result.get("id", 0)
            logger.debug(f"[PixelBridge] {agent_name} → started (id={self._agent_ids[agent_name]})")

    def agent_finished(self, agent_name: str) -> None:
        if not self._enabled:
            return
        self._post("/api/agent/finish", {"agentName": agent_name})
        self._agent_ids.pop(agent_name, None)
        logger.debug(f"[PixelBridge] {agent_name} → finished (waiting)")

    def agent_failed(self, agent_name: str) -> None:
        self.agent_finished(agent_name)

    def finish_all(self) -> None:
        if not self._enabled:
            return
        self._post("/api/agent/finish-all", {})
        self._agent_ids.clear()
        logger.debug("[PixelBridge] finish-all → todos os agentes fechados")
