from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from uuid import UUID
import logging

from src.database.supabase_client import SupabaseClient
from src.database.models import (
    Task, TaskStatus, AgentExecution, TaskResult,
    ExecutionPlan, ExecutionPhase, ReviewStatus
)
from src.agents.base_agent import BaseAgent

# Import de todos os agentes
from src.agents.design.brand_designer import BrandDesignerAgent
from src.agents.design.ux_designer import UXDesignerAgent
from src.agents.design.ui_designer import UIDesignerAgent
from src.agents.design.ux_writer import UXWriterAgent
from src.agents.engineering.frontend_dev import FrontendDevAgent
from src.agents.engineering.mobile_dev import MobileDevAgent
from src.agents.engineering.backend_dev import BackendDevAgent
from src.agents.engineering.tech_lead import TechLeadAgent
from src.agents.quality.qa_engineer import QAEngineerAgent
from src.agents.quality.devops_engineer import DevOpsEngineerAgent

from config.settings import settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orquestrador central que coordena a execução de múltiplos agentes."""

    def __init__(self):
        self.db = SupabaseClient()

        # Registro de todos os agentes disponíveis
        self.agents: Dict[str, BaseAgent] = {
            "brand_designer": BrandDesignerAgent(),
            "ux_designer": UXDesignerAgent(),
            "ui_designer": UIDesignerAgent(),
            "ux_writer": UXWriterAgent(),
            "frontend_dev": FrontendDevAgent(),
            "mobile_dev": MobileDevAgent(),
            "backend_dev": BackendDevAgent(),
            "tech_lead": TechLeadAgent(),
            "qa_engineer": QAEngineerAgent(),
            "devops_engineer": DevOpsEngineerAgent()
        }

    def execute_task(
        self,
        project_id: UUID,
        task_input: str,
        task_type: str = "full_product"
    ) -> Dict[str, Any]:
        """
        Executa uma tarefa completa com orquestração de agentes.

        Args:
            project_id: ID do projeto
            task_input: Descrição da tarefa
            task_type: Tipo da tarefa (determina plano de execução)

        Returns:
            Dict com resultados completos da execução
        """
        # 1. Busca plano de execução
        plan = self.db.get_execution_plan(task_type)
        if not plan:
            raise ValueError(f"Plano de execução não encontrado para: {task_type}")

        # 2. Cria task no banco
        task = self.db.create_task(
            project_id=project_id,
            task_type=task_type,
            input_task=task_input,
            execution_plan=[p.model_dump() for p in plan.phases]
        )

        logger.info(f"Task criada: {task.id} - Tipo: {task_type}")

        # 3. Atualiza status para running
        self.db.update_task_status(task.id, TaskStatus.RUNNING)

        # 4. Busca contexto persistente do projeto
        project_context = self.db.get_project_contexts(project_id)

        results = {
            "task_id": str(task.id),
            "project_id": str(project_id),
            "task_type": task_type,
            "phases": [],
            "agent_outputs": {}
        }

        try:
            # 5. Executa cada fase
            for phase in plan.phases:
                phase_result = self._execute_phase(
                    task=task,
                    phase=phase,
                    task_input=task_input,
                    project_context=project_context
                )
                results["phases"].append(phase_result)
                results["agent_outputs"].update(phase_result["outputs"])

            # 6. Consolida resultado final
            final_output = self._consolidate_outputs(results["agent_outputs"])
            summary = self._generate_summary(results["agent_outputs"])

            # 7. Salva resultado
            task_result = TaskResult(
                task_id=task.id,
                final_output=final_output,
                summary=summary,
                deliverables=self._extract_deliverables(results["agent_outputs"]),
                review_status=ReviewStatus.PENDING
            )
            self.db.save_task_result(task_result)

            # 8. Atualiza status
            self.db.update_task_status(task.id, TaskStatus.COMPLETED)

            results["final_output"] = final_output
            results["summary"] = summary
            results["status"] = "completed"

            logger.info(f"Task completada: {task.id}")

        except Exception as e:
            logger.error(f"Erro na task {task.id}: {str(e)}")
            self.db.update_task_status(task.id, TaskStatus.FAILED, str(e))
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    def _execute_phase(
        self,
        task: Task,
        phase: ExecutionPhase,
        task_input: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa uma fase (múltiplos agentes, potencialmente em paralelo)."""

        # Coleta outputs de fases anteriores como contexto
        previous_outputs = self.db.get_phase_outputs(task.id, phase.phase)

        phase_result = {
            "phase": phase.phase,
            "agents": phase.agents,
            "parallel": phase.parallel,
            "outputs": {}
        }

        if phase.parallel and len(phase.agents) > 1:
            # Execução paralela
            with ThreadPoolExecutor(max_workers=settings.max_parallel_agents) as executor:
                futures = {
                    executor.submit(
                        self._execute_agent,
                        agent_name=agent_name,
                        task=task,
                        phase=phase,
                        task_input=task_input,
                        context=previous_outputs,
                        project_context=project_context
                    ): agent_name
                    for agent_name in phase.agents
                }

                for future in as_completed(futures):
                    agent_name = futures[future]
                    try:
                        execution = future.result()
                        phase_result["outputs"][agent_name] = execution.output_text
                    except Exception as e:
                        logger.error(f"Erro no agente {agent_name}: {str(e)}")
                        phase_result["outputs"][agent_name] = f"ERRO: {str(e)}"
        else:
            # Execução sequencial
            for agent_name in phase.agents:
                execution = self._execute_agent(
                    agent_name=agent_name,
                    task=task,
                    phase=phase,
                    task_input=task_input,
                    context=previous_outputs,
                    project_context=project_context
                )
                phase_result["outputs"][agent_name] = execution.output_text
                # Atualiza contexto para próximo agente na mesma fase
                previous_outputs[agent_name] = execution.output_text

        return phase_result

    def _execute_agent(
        self,
        agent_name: str,
        task: Task,
        phase: ExecutionPhase,
        task_input: str,
        context: Dict[str, str],
        project_context: Dict[str, Any]
    ) -> AgentExecution:
        """Executa um agente individual."""

        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agente não encontrado: {agent_name}")

        logger.info(f"Executando agente: {agent_name} (fase {phase.phase})")

        execution = agent.execute(
            task=task_input,
            context=context,
            project_context=project_context,
            task_id=task.id,
            phase_number=phase.phase
        )

        # Salva execução no banco
        self.db.save_agent_execution(execution)

        return execution

    def _consolidate_outputs(self, outputs: Dict[str, str]) -> str:
        """Consolida todos os outputs em um documento final."""
        sections = []

        # Ordem lógica de apresentação
        order = [
            "brand_designer", "ux_designer", "ux_writer", "ui_designer",
            "tech_lead", "frontend_dev", "backend_dev", "mobile_dev",
            "qa_engineer", "devops_engineer"
        ]

        for agent_name in order:
            if agent_name in outputs:
                title = agent_name.replace("_", " ").title()
                sections.append(f"{'='*70}\n## {title}\n{'='*70}\n\n{outputs[agent_name]}")

        # Adiciona agentes não listados na ordem
        for agent_name, output in outputs.items():
            if agent_name not in order:
                title = agent_name.replace("_", " ").title()
                sections.append(f"{'='*70}\n## {title}\n{'='*70}\n\n{output}")

        return "\n\n".join(sections)

    def _generate_summary(self, outputs: Dict[str, str]) -> str:
        """Gera sumário executivo dos outputs."""
        agents_executed = list(outputs.keys())
        return f"Execução completa com {len(agents_executed)} agentes: {', '.join(agents_executed)}"

    def _extract_deliverables(self, outputs: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extrai lista de entregáveis dos outputs."""
        deliverables = []

        # Mapeamento de agente para tipo de entregável
        agent_deliverables = {
            "brand_designer": "Identidade Visual e Brandbook",
            "ux_designer": "Wireframes e Fluxos de Usuário",
            "ui_designer": "Design de Alta Fidelidade",
            "ux_writer": "Textos e Microcopy",
            "tech_lead": "Arquitetura Técnica",
            "frontend_dev": "Código Frontend",
            "backend_dev": "Código Backend",
            "mobile_dev": "Código Mobile",
            "qa_engineer": "Plano de Testes",
            "devops_engineer": "Configuração de Infraestrutura"
        }

        for agent_name in outputs.keys():
            if agent_name in agent_deliverables:
                deliverables.append({
                    "type": agent_deliverables[agent_name],
                    "agent": agent_name,
                    "status": "completed"
                })

        return deliverables

    def get_available_agents(self) -> Dict[str, List[str]]:
        """Retorna todos os agentes disponíveis e suas capacidades."""
        return {
            name: agent.get_capabilities()
            for name, agent in self.agents.items()
        }

    def get_execution_plans(self) -> List[str]:
        """Retorna tipos de planos de execução disponíveis."""
        return [
            "full_product",
            "mobile_app",
            "design_only",
            "dev_only",
            "quick_ui"
        ]
