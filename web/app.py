import os
import sys
import threading
import logging
import time
from pathlib import Path
from uuid import UUID
from flask import Flask, render_template, request, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.database.supabase_client import SupabaseClient
from src.orchestrator import Orchestrator
from src.deployer import deploy_build

# ── Definição dos Squads ──────────────────────────────────────────────────────
SQUADS = {
    "criacao": {
        "id": "criacao",
        "name": "Squad de Criação",
        "icon": "🎨",
        "description": "Marca, identidade visual, UX e microcopy. Ideal para criar a personalidade e experiência do produto.",
        "color": "purple",
        "agents": ["brand_designer", "ux_designer", "ui_designer", "ux_writer"],
        "agent_labels": ["Brand Designer", "UX Designer", "UI Designer", "UX Writer"],
    },
    "desenvolvimento": {
        "id": "desenvolvimento",
        "name": "Squad de Desenvolvimento",
        "icon": "💻",
        "description": "Arquitetura, frontend, backend e mobile. Para construir o produto com solidez técnica.",
        "color": "blue",
        "agents": ["tech_lead", "frontend_dev", "backend_dev", "mobile_dev"],
        "agent_labels": ["Tech Lead", "Frontend Dev", "Backend Dev", "Mobile Dev"],
    },
    "delivery": {
        "id": "delivery",
        "name": "Squad de Delivery",
        "icon": "🚀",
        "description": "Qualidade, infraestrutura e lançamento. Para garantir que o produto chegue ao ar com excelência.",
        "color": "green",
        "agents": ["tech_lead", "qa_engineer", "devops_engineer"],
        "agent_labels": ["Tech Lead", "QA Engineer", "DevOps Engineer"],
    },
}

PIXEL_AGENTS_URL = os.environ.get("PIXEL_AGENTS_URL", "http://localhost:3456")

app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

db = SupabaseClient()
orchestrator = Orchestrator()

# { run_id: { status, progress: [...], result, error } }
_running_tasks = {}


def _make_progress_callback(run_id):
    def callback(agent_name, phase, status, output_text, tokens_in, tokens_out, time_ms):
        task = _running_tasks.get(run_id)
        if not task:
            return

        # Atualiza entrada existente ou cria nova
        existing = next((p for p in task["progress"] if p["agent"] == agent_name), None)
        if existing:
            existing["status"] = status
            existing["output_text"] = output_text
            existing["tokens_input"] = tokens_in
            existing["tokens_output"] = tokens_out
            existing["execution_time_ms"] = time_ms
            existing["finished_at"] = time.time() if status in ("completed", "failed") else None
        else:
            task["progress"].append({
                "agent": agent_name,
                "phase": phase,
                "status": status,
                "output_text": output_text,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "execution_time_ms": time_ms,
                "started_at": time.time(),
                "finished_at": time.time() if status in ("completed", "failed") else None,
            })
    return callback


def _run_task_background(run_id, project_id, task_input, task_type, agent_list=None):
    _running_tasks[run_id] = {
        "status": "running",
        "progress": [],
        "result": None,
        "error": None,
        "started_at": time.time(),
        "task_type": task_type
    }
    try:
        result = orchestrator.execute_task(
            project_id=UUID(project_id),
            task_input=task_input,
            task_type=task_type,
            progress_callback=_make_progress_callback(run_id),
            agent_list=agent_list
        )
        _running_tasks[run_id]["result"] = result
        _running_tasks[run_id]["status"] = result.get("status", "completed")

        # Gera build estático e retorna URL do entregável
        agent_outputs = result.get("agent_outputs", {})
        if agent_outputs:
            try:
                deploy_url, deploy_source = deploy_build(run_id, agent_outputs)
                _running_tasks[run_id]["deploy_url"] = deploy_url
                _running_tasks[run_id]["deploy_source"] = deploy_source
            except Exception as deploy_err:
                _running_tasks[run_id]["deploy_url"] = None

    except Exception as e:
        _running_tasks[run_id]["status"] = "failed"
        _running_tasks[run_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html", pixel_agents_url=PIXEL_AGENTS_URL)


@app.route("/api/agents")
def list_agents():
    return jsonify(orchestrator.get_available_agents())


@app.route("/api/squads")
def list_squads():
    return jsonify(list(SQUADS.values()))


@app.route("/api/projects", methods=["GET"])
def list_projects():
    projects = db.list_projects()
    return jsonify([{
        "id": str(p.id),
        "name": p.name,
        "description": p.description or "",
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in projects])


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    if not name:
        return jsonify({"error": "Nome é obrigatório"}), 400
    project = db.create_project(name, description)
    return jsonify({"id": str(project.id), "name": project.name}), 201


@app.route("/api/run", methods=["POST"])
def run_task():
    data = request.json
    project_id = data.get("project_id")
    task_input = data.get("task_input", "").strip()
    task_type = data.get("task_type", "full_product")
    agent_list = data.get("agent_list", None)   # lista de agentes do squad

    if not project_id or not task_input:
        return jsonify({"error": "project_id e task_input são obrigatórios"}), 400

    import uuid
    run_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=_run_task_background,
        args=(run_id, project_id, task_input, task_type, agent_list),
        daemon=True
    )
    thread.start()

    return jsonify({"run_id": run_id, "status": "running"}), 202


@app.route("/api/run/<run_id>")
def get_run_status(run_id):
    run = _running_tasks.get(run_id)
    if not run:
        return jsonify({"error": "Run não encontrado"}), 404

    response = {
        "status": run["status"],
        "progress": run["progress"],
        "elapsed": round(time.time() - run["started_at"], 1)
    }

    if run["status"] in ("completed", "failed") and run["result"]:
        result = run["result"]
        response["task_id"] = result.get("task_id")
        response["agent_outputs"] = result.get("agent_outputs", {})

    if run["error"]:
        response["error"] = run["error"]

    if run.get("deploy_url"):
        response["deploy_url"] = run["deploy_url"]
        response["deploy_source"] = run.get("deploy_source", "")

    response["task_type"] = run.get("task_type", "")

    return jsonify(response)


@app.route("/api/deploy", methods=["POST"])
def deploy_outputs():
    """Gera build estático a partir de agent_outputs e retorna URL."""
    data = request.json
    run_id = data.get("run_id", "")
    agent_outputs = data.get("agent_outputs", {})
    if not run_id or not agent_outputs:
        return jsonify({"error": "run_id e agent_outputs são obrigatórios"}), 400
    try:
        url, source = deploy_build(run_id, agent_outputs)
        return jsonify({"deploy_url": url, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<project_id>")
def list_tasks(project_id):
    tasks = db.list_project_tasks(UUID(project_id))
    result = []
    for t in tasks:
        task_result = db.get_task_result(t.id)
        result.append({
            "id": str(t.id),
            "task_type": t.task_type,
            "input_task": t.input_task,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "has_result": task_result is not None
        })
    return jsonify(result)


@app.route("/api/task-result/<task_id>")
def get_task_result(task_id):
    executions = db.get_task_executions(UUID(task_id))
    result = db.get_task_result(UUID(task_id))
    return jsonify({
        "executions": [{
            "agent_name": e.agent_name,
            "output_text": e.output_text,
            "status": e.status,
            "tokens_input": e.tokens_input,
            "tokens_output": e.tokens_output,
            "execution_time_ms": e.execution_time_ms,
            "phase_number": e.phase_number
        } for e in executions],
        "final_output": result.final_output if result else "",
        "summary": result.summary if result else ""
    })


@app.route("/api/pixel/start", methods=["POST"])
def pixel_start():
    """Dispara animação de um agente no Pixel Office (demo)."""
    data = request.json or {}
    agent_name = data.get("agent_name", "").strip()
    if not agent_name:
        return jsonify({"error": "agent_name é obrigatório"}), 400
    try:
        orchestrator.pixel.agent_started(agent_name)
        return jsonify({"ok": True, "agent": agent_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pixel/finish", methods=["POST"])
def pixel_finish():
    """Finaliza animação de um agente no Pixel Office (demo)."""
    data = request.json or {}
    agent_name = data.get("agent_name", "").strip()
    if not agent_name:
        return jsonify({"error": "agent_name é obrigatório"}), 400
    try:
        orchestrator.pixel.agent_finished(agent_name)
        return jsonify({"ok": True, "agent": agent_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pixel/finish-all", methods=["POST"])
def pixel_finish_all():
    """Finaliza animações de todos os agentes ativos no Pixel Office."""
    try:
        orchestrator.pixel.finish_all()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  Agent Orchestrator — Interface Web")
    print("  Acesse: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000, threaded=True)
