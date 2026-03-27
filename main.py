import argparse
import sys
from uuid import UUID

from src.orchestrator import Orchestrator
from src.database.supabase_client import SupabaseClient
from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()


def main():
    parser = argparse.ArgumentParser(description="Orquestrador Multi-Agente")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: new-project
    new_project = subparsers.add_parser("new-project", help="Cria novo projeto")
    new_project.add_argument("name", help="Nome do projeto")
    new_project.add_argument("--description", "-d", default="", help="Descrição")

    # Comando: list-projects
    subparsers.add_parser("list-projects", help="Lista projetos")

    # Comando: run
    run = subparsers.add_parser("run", help="Executa uma tarefa")
    run.add_argument("project_id", help="ID do projeto")
    run.add_argument("task", help="Descrição da tarefa")
    run.add_argument("--type", "-t", default="full_product",
                     choices=["full_product", "mobile_app", "design_only", "dev_only", "quick_ui"],
                     help="Tipo da tarefa")
    run.add_argument("--output", "-o", help="Arquivo para salvar output")

    # Comando: status
    status = subparsers.add_parser("status", help="Verifica status de uma tarefa")
    status.add_argument("task_id", help="ID da tarefa")

    # Comando: agents
    subparsers.add_parser("agents", help="Lista agentes disponíveis")

    args = parser.parse_args()

    if not settings.validate():
        print("Erro: Configure ANTHROPIC_API_KEY, SUPABASE_URL e SUPABASE_KEY no .env")
        sys.exit(1)

    db = SupabaseClient()
    orchestrator = Orchestrator()

    if args.command == "new-project":
        project = db.create_project(args.name, args.description)
        print(f"Projeto criado: {project.id}")
        print(f"   Nome: {project.name}")

    elif args.command == "list-projects":
        projects = db.list_projects()
        if not projects:
            print("Nenhum projeto encontrado.")
        else:
            print(f"{'ID':<40} {'Nome':<30} {'Status':<10}")
            print("-" * 80)
            for p in projects:
                print(f"{str(p.id):<40} {p.name:<30} {p.status:<10}")

    elif args.command == "run":
        print(f"Iniciando execucao...")
        print(f"   Projeto: {args.project_id}")
        print(f"   Tipo: {args.type}")
        print(f"   Tarefa: {args.task[:100]}...")
        print()

        result = orchestrator.execute_task(
            project_id=UUID(args.project_id),
            task_input=args.task,
            task_type=args.type
        )

        if result["status"] == "completed":
            print(f"Tarefa completada: {result['task_id']}")
            print(f"   Fases executadas: {len(result['phases'])}")
            print(f"   Agentes: {', '.join(result['agent_outputs'].keys())}")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result["final_output"])
                print(f"   Output salvo em: {args.output}")
            else:
                print("\n" + "="*70)
                print(result["final_output"])
        else:
            print(f"Erro: {result.get('error', 'Erro desconhecido')}")

    elif args.command == "status":
        task = db.get_task(UUID(args.task_id))
        if task:
            print(f"Task: {task.id}")
            print(f"Status: {task.status}")
            print(f"Tipo: {task.task_type}")
            print(f"Criada: {task.created_at}")
            if task.completed_at:
                print(f"Completada: {task.completed_at}")
            if task.error_message:
                print(f"Erro: {task.error_message}")
        else:
            print(f"Task nao encontrada: {args.task_id}")

    elif args.command == "agents":
        agents = orchestrator.get_available_agents()
        print(f"{'Agente':<20} {'Capacidades'}")
        print("-" * 70)
        for name, caps in agents.items():
            print(f"{name:<20} {', '.join(caps[:3])}...")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
