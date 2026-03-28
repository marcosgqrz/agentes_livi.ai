import sys
import threading
import logging
from pathlib import Path
from uuid import UUID
from flask import Flask, render_template, request, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.database.supabase_client import SupabaseClient
from src.orchestrator import Orchestrator

app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

db = SupabaseClient()
orchestrator = Orchestrator()

# Tasks running in background
_running_tasks = {}


def _run_task_background(task_run_id, project_id, task_input, task_type):
    _running_tasks[task_run_id] = {"status": "running", "result": None, "error": None}
    try:
        result = orchestrator.execute_task(
            project_id=UUID(project_id),
            task_input=task_input,
            task_type=task_type
        )
        _running_tasks[task_run_id]["result"] = result
        _running_tasks[task_run_id]["status"] = result.get("status", "completed")
    except Exception as e:
        _running_tasks[task_run_id]["status"] = "failed"
        _running_tasks[task_run_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/agents")
def list_agents():
    agents = orchestrator.get_available_agents()
    return jsonify(agents)


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

    if not project_id or not task_input:
        return jsonify({"error": "project_id e task_input são obrigatórios"}), 400

    import uuid
    run_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=_run_task_background,
        args=(run_id, project_id, task_input, task_type),
        daemon=True
    )
    thread.start()

    return jsonify({"run_id": run_id, "status": "running"}), 202


@app.route("/api/run/<run_id>")
def get_run_status(run_id):
    run = _running_tasks.get(run_id)
    if not run:
        return jsonify({"error": "Run não encontrado"}), 404

    response = {"status": run["status"]}

    if run["status"] in ("completed", "failed") and run["result"]:
        result = run["result"]
        response["task_id"] = result.get("task_id")
        response["agents"] = list(result.get("agent_outputs", {}).keys())
        response["phases"] = len(result.get("phases", []))
        response["agent_outputs"] = result.get("agent_outputs", {})
        response["final_output"] = result.get("final_output", "")

    if run["error"]:
        response["error"] = run["error"]

    return jsonify(response)


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


if __name__ == "__main__":
    print("=" * 50)
    print("  Agent Orchestrator — Interface Web")
    print("  Acesse: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000, threaded=True)
