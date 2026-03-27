from abc import ABC, abstractmethod
from anthropic import Anthropic
from typing import Dict, Any
from pathlib import Path
import time
from uuid import UUID

from config.settings import settings
from src.database.models import AgentExecution, AgentCategory


class BaseAgent(ABC):
    """Classe base para todos os agentes especializados."""

    def __init__(
        self,
        name: str,
        category: AgentCategory,
        prompt_file: str
    ):
        self.name = name
        self.category = category
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.system_prompt = self._load_prompt(prompt_file)

    def _load_prompt(self, prompt_file: str) -> str:
        """Carrega o system prompt do arquivo."""
        prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")

    def execute(
        self,
        task: str,
        context: Dict[str, str] = None,
        project_context: Dict[str, Any] = None,
        task_id: UUID = None,
        phase_number: int = 1
    ) -> AgentExecution:
        """
        Executa o agente com a tarefa e contexto fornecidos.

        Args:
            task: Descrição da tarefa
            context: Outputs de agentes anteriores (fase anterior)
            project_context: Contexto persistente do projeto (brand, design system, etc)
            task_id: ID da tarefa para registro
            phase_number: Número da fase de execução

        Returns:
            AgentExecution com input, output e métricas
        """
        start_time = time.time()

        # Monta mensagem com contexto
        full_task = self._build_task_with_context(task, context, project_context)

        try:
            response = self.client.messages.create(
                model=settings.model,
                max_tokens=settings.max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": full_task}]
            )

            output_text = response.content[0].text
            execution_time = int((time.time() - start_time) * 1000)

            # Tenta extrair estrutura do output
            output_structured = self._extract_structured_output(output_text)

            return AgentExecution(
                task_id=task_id,
                agent_name=self.name,
                agent_category=self.category,
                phase_number=phase_number,
                input_context={"task": task, "context_keys": list(context.keys()) if context else []},
                output_text=output_text,
                output_structured=output_structured,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                execution_time_ms=execution_time,
                status="completed"
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return AgentExecution(
                task_id=task_id,
                agent_name=self.name,
                agent_category=self.category,
                phase_number=phase_number,
                input_context={"task": task},
                output_text="",
                execution_time_ms=execution_time,
                status="failed",
                error_message=str(e)
            )

    def _build_task_with_context(
        self,
        task: str,
        context: Dict[str, str] = None,
        project_context: Dict[str, Any] = None
    ) -> str:
        """Monta a mensagem completa com contextos."""
        parts = []

        # Contexto persistente do projeto
        if project_context:
            parts.append("## CONTEXTO DO PROJETO\n")
            for ctx_type, ctx_data in project_context.items():
                parts.append(f"### {ctx_type.upper()}\n{self._format_context(ctx_data)}\n")

        # Outputs de agentes anteriores
        if context:
            parts.append("## OUTPUTS DE AGENTES ANTERIORES\n")
            for agent_name, output in context.items():
                parts.append(f"### {agent_name.upper()}\n{output}\n")

        # Tarefa atual
        parts.append(f"## SUA TAREFA\n{task}")

        return "\n".join(parts)

    def _format_context(self, ctx_data: Any) -> str:
        """Formata contexto para inclusão no prompt."""
        if isinstance(ctx_data, dict):
            return "\n".join([f"- **{k}**: {v}" for k, v in ctx_data.items()])
        return str(ctx_data)

    def _extract_structured_output(self, output: str) -> Dict[str, Any]:
        """
        Tenta extrair dados estruturados do output.
        Sobrescreva nos agentes específicos para parsing customizado.
        """
        return {}

    @abstractmethod
    def get_capabilities(self) -> list:
        """Retorna lista de capacidades do agente."""
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, str]:
        """Retorna schema esperado do output."""
        pass
