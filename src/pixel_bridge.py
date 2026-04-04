"""
pixel_bridge.py — Integração com pixel-agents-standalone

Escreve arquivos JSONL sintéticos em ~/.claude/projects/ durante a execução
dos agentes do orchestrator. O pixel-agents detecta esses arquivos e exibe
cada agente como um personagem animado no escritório pixel art.

Formato JSONL esperado pelo pixel-agents:
  - tool_use  → personagem "digitando" ou "lendo"
  - tool_result → ferramenta concluída
  - system/turn_duration → personagem "aguardando" (idle)
"""

import json
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Qual "ferramenta" simular para cada agente (define a animação)
# "Edit"  → typing (escrever código/doc)
# "Read"  → reading (leitura/pesquisa)
# "Bash"  → running (executar)
_AGENT_TOOL = {
    "brand_designer":  ("Edit",  "brand-guidelines.md"),
    "ux_designer":     ("Read",  "ux-research.md"),
    "ui_designer":     ("Edit",  "design-system.md"),
    "ux_writer":       ("Edit",  "microcopy.md"),
    "tech_lead":       ("Read",  "architecture.md"),
    "frontend_dev":    ("Edit",  "src/App.tsx"),
    "backend_dev":     ("Edit",  "src/api/routes.py"),
    "mobile_dev":      ("Edit",  "src/screens/Home.tsx"),
    "qa_engineer":     ("Bash",  "npm test --coverage"),
    "devops_engineer": ("Bash",  "docker compose up -d"),
}


class PixelAgentSession:
    """Sessão JSONL sintética para um único agente."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.session_id = str(uuid.uuid4())
        # Dir name sem hífens → projectName = agent_name (última parte do split por "-")
        self.project_dir = CLAUDE_PROJECTS_DIR / agent_name
        self.jsonl_path = self.project_dir / f"{self.session_id}.jsonl"
        self._tool_id = f"toolu_{uuid.uuid4().hex[:16]}"
        self._active = False

    def start(self) -> None:
        """Cria o arquivo e escreve o evento tool_use → personagem ativa."""
        try:
            self.project_dir.mkdir(parents=True, exist_ok=True)

            tool_name, file_ref = _AGENT_TOOL.get(self.agent_name, ("Edit", "output.md"))

            if tool_name == "Bash":
                input_block = {"command": file_ref}
            else:
                input_block = {"file_path": file_ref}

            line = json.dumps({
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": self._tool_id,
                        "name": tool_name,
                        "input": input_block
                    }]
                }
            }, ensure_ascii=False)

            self.jsonl_path.write_text(line + "\n", encoding="utf-8")
            self._active = True
            logger.debug(f"[PixelBridge] {self.agent_name} → started ({tool_name})")
        except Exception as e:
            logger.warning(f"[PixelBridge] Falha ao iniciar sessão de {self.agent_name}: {e}")

    def finish(self) -> None:
        """Escreve tool_result + turn_duration → personagem vai para waiting/idle."""
        if not self._active:
            return
        try:
            result_line = json.dumps({
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": self._tool_id,
                        "content": []
                    }]
                }
            }, ensure_ascii=False)

            turn_line = json.dumps({
                "type": "system",
                "subtype": "turn_duration",
                "durationMs": 1000
            })

            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(result_line + "\n")
                f.write(turn_line + "\n")

            self._active = False
            logger.debug(f"[PixelBridge] {self.agent_name} → finished (waiting)")
        except Exception as e:
            logger.warning(f"[PixelBridge] Falha ao finalizar sessão de {self.agent_name}: {e}")


class PixelAgentsBridge:
    """
    Gerencia sessões pixel para todos os agentes do orchestrator.

    Uso no orchestrator:
        bridge = PixelAgentsBridge()
        bridge.agent_started("brand_designer")   # antes de agent.execute()
        bridge.agent_finished("brand_designer")  # depois de agent.execute()
    """

    def __init__(self):
        self._sessions: dict[str, PixelAgentSession] = {}
        # Verifica se o pixel-agents está rodando (não bloqueia se não estiver)
        self._enabled = self._check_pixel_agents()

    def _check_pixel_agents(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:3456/", timeout=1)
            logger.info("[PixelBridge] pixel-agents detectado em localhost:3456 ✓")
            return True
        except Exception:
            logger.info("[PixelBridge] pixel-agents não encontrado — bridge desativada")
            return False

    def agent_started(self, agent_name: str) -> None:
        if not self._enabled:
            return
        # Encerra sessão anterior se houver (segurança)
        self._close_session(agent_name)
        session = PixelAgentSession(agent_name)
        session.start()
        self._sessions[agent_name] = session

    def agent_finished(self, agent_name: str) -> None:
        if not self._enabled:
            return
        self._close_session(agent_name)

    def agent_failed(self, agent_name: str) -> None:
        if not self._enabled:
            return
        self._close_session(agent_name)

    def finish_all(self) -> None:
        for name in list(self._sessions.keys()):
            self._close_session(name)

    def _close_session(self, agent_name: str) -> None:
        session = self._sessions.pop(agent_name, None)
        if session:
            session.finish()
