import argparse
import sys
from uuid import UUID

from src.orchestrator import Orchestrator
from src.database.supabase_client import create_db_client
from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()

# Squads disponíveis (mesmos do web/app.py)
SQUADS = {
    "criacao": {
        "name": "Squad de Criação",
        "agents": ["brand_designer", "ux_designer", "ui_designer", "ux_writer"],
        "description": "Marca, identidade visual, UX e microcopy",
    },
    "desenvolvimento": {
        "name": "Squad de Desenvolvimento",
        "agents": ["tech_lead", "frontend_dev", "backend_dev", "mobile_dev"],
        "description": "Arquitetura, frontend, backend e mobile",
    },
    "delivery": {
        "name": "Squad de Delivery",
        "agents": ["tech_lead", "qa_engineer", "devops_engineer"],
        "description": "Qualidade, infraestrutura e lançamento",
    },
    "crescimento": {
        "name": "Squad de Crescimento",
        "agents": ["traffic_manager", "seo_specialist", "social_media_strategist"],
        "description": "Tráfego pago, SEO e social media",
    },
    "negocios": {
        "name": "Squad de Negócios",
        "agents": ["sales_representative", "customer_success", "bi_insights_agent"],
        "description": "Vendas B2B, customer success e BI",
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador Multi-Agente — CLI + Web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py web                          # Inicia interface web (http://localhost:5000)
  python main.py agents                       # Lista todos os 16 agentes
  python main.py squads                       # Lista squads disponíveis
  python main.py new-project "Meu SaaS"
  python main.py run <PROJECT_ID> "Criar landing page" --type full_product
  python main.py run <PROJECT_ID> "Estratégia de marketing" --squad crescimento
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: web
    web_cmd = subparsers.add_parser("web", help="Inicia a interface web Flask")
    web_cmd.add_argument("--port", "-p", type=int, default=5000, help="Porta (padrão: 5000)")
    web_cmd.add_argument("--debug", action="store_true", help="Modo debug")

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
    run.add_argument(
        "--type", "-t", default="full_product",
        choices=[
            "full_product", "mobile_app", "design_only", "dev_only", "quick_ui",
            "growth_only", "business_only", "full_go_to_market"
        ],
        help="Tipo da tarefa (padrão: full_product)"
    )
    run.add_argument(
        "--squad", "-s",
        choices=list(SQUADS.keys()),
        help="Executa usando um squad específico (sobrepõe --type)"
    )
    run.add_argument("--output", "-o", help="Arquivo para salvar output")

    # Comando: status
    status = subparsers.add_parser("status", help="Verifica status de uma tarefa")
    status.add_argument("task_id", help="ID da tarefa")

    # Comando: agents
    subparsers.add_parser("agents", help="Lista todos os agentes disponíveis")

    # Comando: squads
    subparsers.add_parser("squads", help="Lista squads disponíveis")

    args = parser.parse_args()

    # Sem comando: mostra ajuda
    if not args.command:
        parser.print_help()
        return

    # Comando web não precisa das chaves — apenas lança o app
    if args.command == "web":
        _start_web(port=args.port, debug=args.debug)
        return

    # Verifica pelo menos a chave da Anthropic
    if not settings.has_anthropic():
        print("Erro: Configure ANTHROPIC_API_KEY no .env")
        print("      Supabase é opcional — sem ele os dados ficam em memória (modo dev).")
        sys.exit(1)

    if settings.dev_mode:
        print("[modo dev] Supabase não configurado — dados ficam em memória.")

    db = create_db_client()
    orchestrator = Orchestrator(db)

    # ── Comandos ──────────────────────────────────────────────────────────────

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
        # Resolve squad → agent_list e task_type
        agent_list = None
        task_type = args.type

        if args.squad:
            squad = SQUADS[args.squad]
            agent_list = squad["agents"]
            task_type = f"squad_{args.squad}"
            print(f"Squad: {squad['name']} ({', '.join(squad['agents'])})")

        print(f"Iniciando execucao...")
        print(f"   Projeto : {args.project_id}")
        print(f"   Tipo    : {task_type}")
        print(f"   Tarefa  : {args.task[:100]}...")
        print()

        result = orchestrator.execute_task(
            project_id=UUID(args.project_id),
            task_input=args.task,
            task_type=task_type,
            agent_list=agent_list
        )

        if result["status"] == "completed":
            print(f"Tarefa completada: {result['task_id']}")
            print(f"   Fases executadas : {len(result['phases'])}")
            print(f"   Agentes          : {', '.join(result['agent_outputs'].keys())}")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result["final_output"])
                print(f"   Output salvo em  : {args.output}")
            else:
                print("\n" + "=" * 70)
                print(result["final_output"])
        else:
            print(f"Erro: {result.get('error', 'Erro desconhecido')}")

    elif args.command == "status":
        task = db.get_task(UUID(args.task_id))
        if task:
            print(f"Task    : {task.id}")
            print(f"Status  : {task.status}")
            print(f"Tipo    : {task.task_type}")
            print(f"Criada  : {task.created_at}")
            if task.completed_at:
                print(f"Concluída: {task.completed_at}")
            if task.error_message:
                print(f"Erro    : {task.error_message}")
        else:
            print(f"Task não encontrada: {args.task_id}")

    elif args.command == "agents":
        agents = orchestrator.get_available_agents()
        print(f"{'Agente':<30} {'Categoria':<15} {'Capacidades'}")
        print("-" * 80)
        # Agrupa por categoria
        categories = {}
        for name, caps in agents.items():
            for agent_obj in [orchestrator.agents[name]]:
                cat = agent_obj.category.value
                categories.setdefault(cat, []).append((name, caps))
        for cat in ["design", "engineering", "quality", "growth", "business"]:
            if cat not in categories:
                continue
            print(f"\n[{cat.upper()}]")
            for name, caps in categories[cat]:
                print(f"  {name:<28} {', '.join(caps[:3])}...")

    elif args.command == "squads":
        print(f"{'Squad':<15} {'Nome':<25} {'Agentes'}")
        print("-" * 80)
        for squad_id, squad in SQUADS.items():
            print(f"  {squad_id:<13} {squad['name']:<25} {', '.join(squad['agents'])}")
            print(f"  {'':13} {squad['description']}")
            print()


def _start_web(port: int = 5000, debug: bool = False):
    """Inicia o servidor Flask."""
    import os
    import sys

    web_dir = os.path.join(os.path.dirname(__file__), "web")
    sys.path.insert(0, web_dir)

    # Importa e roda o app Flask
    from web.app import app

    print("=" * 50)
    print("  Agent Orchestrator — Interface Web")
    print(f"  Acesse: http://localhost:{port}")
    if settings.dev_mode:
        print("  [modo dev] dados em memória (sem Supabase)")
    print("=" * 50)

    app.run(debug=debug, port=port, threaded=True)


if __name__ == "__main__":
    main()
