import os
import sys
import threading
import logging
import time
import json
import io
import base64
from pathlib import Path
from uuid import UUID
from flask import Flask, render_template, request, jsonify, send_from_directory

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.database.supabase_client import create_db_client
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
    "crescimento": {
        "id": "crescimento",
        "name": "Squad de Crescimento",
        "icon": "📈",
        "description": "Tráfego pago, SEO e social media. Para atrair usuários e construir presença digital.",
        "color": "orange",
        "agents": ["traffic_manager", "seo_specialist", "social_media_strategist"],
        "agent_labels": ["Traffic Manager", "SEO Specialist", "Social Media Strategist"],
    },
    "negocios": {
        "id": "negocios",
        "name": "Squad de Negócios",
        "icon": "💼",
        "description": "Vendas B2B, customer success e inteligência de dados. Para converter e reter clientes.",
        "color": "yellow",
        "agents": ["sales_representative", "customer_success", "bi_insights_agent"],
        "agent_labels": ["Sales Representative", "Customer Success", "BI Insights Agent"],
    },
}

PIXEL_AGENTS_URL = os.environ.get("PIXEL_AGENTS_URL", "http://localhost:3456")

app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)

db = create_db_client()
orchestrator = Orchestrator(db)

if settings.dev_mode:
    logger.warning("=" * 60)
    logger.warning("MODO DEV  —  armazenamento em memória ativo.")
    logger.warning("Configure SUPABASE_URL e SUPABASE_KEY para persistência.")
    logger.warning("=" * 60)

if not settings.has_anthropic():
    logger.warning("ANTHROPIC_API_KEY ausente — agentes retornarão erro ao executar.")

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


# ── Parametrização de Agentes ─────────────────────────────────────────────────

AGENT_META = {
    "brand_designer":          {"label": "Brand Designer",           "category": "design",      "icon": "🎨"},
    "ux_designer":             {"label": "UX Designer",               "category": "design",      "icon": "🔍"},
    "ui_designer":             {"label": "UI Designer",               "category": "design",      "icon": "🖼️"},
    "ux_writer":               {"label": "UX Writer",                 "category": "design",      "icon": "✍️"},
    "tech_lead":               {"label": "Tech Lead",                 "category": "engineering", "icon": "🏗️"},
    "frontend_dev":            {"label": "Frontend Dev",              "category": "engineering", "icon": "💻"},
    "backend_dev":             {"label": "Backend Dev",               "category": "engineering", "icon": "⚙️"},
    "mobile_dev":              {"label": "Mobile Dev",                "category": "engineering", "icon": "📱"},
    "qa_engineer":             {"label": "QA Engineer",               "category": "quality",     "icon": "🧪"},
    "devops_engineer":         {"label": "DevOps Engineer",           "category": "quality",     "icon": "🚀"},
    "traffic_manager":         {"label": "Traffic Manager",           "category": "growth",      "icon": "📊"},
    "seo_specialist":          {"label": "SEO Specialist",            "category": "growth",      "icon": "🔎"},
    "social_media_strategist": {"label": "Social Media Strategist",   "category": "growth",      "icon": "📣"},
    "sales_representative":    {"label": "Sales Representative",      "category": "business",    "icon": "💼"},
    "customer_success":        {"label": "Customer Success",          "category": "business",    "icon": "🤝"},
    "bi_insights_agent":       {"label": "BI Insights Agent",         "category": "business",    "icon": "📈"},
}

PROMPT_CATEGORY_MAP = {
    "brand_designer": "design", "ux_designer": "design",
    "ui_designer": "design", "ux_writer": "design",
    "tech_lead": "engineering", "frontend_dev": "engineering",
    "backend_dev": "engineering", "mobile_dev": "engineering",
    "qa_engineer": "quality", "devops_engineer": "quality",
    "traffic_manager": "growth", "seo_specialist": "growth",
    "social_media_strategist": "growth",
    "sales_representative": "business", "customer_success": "business",
    "bi_insights_agent": "business",
}

PROMPTS_BASE = Path(__file__).parent.parent / "src" / "prompts"


def _prompt_path(agent_name: str) -> Path:
    cat = PROMPT_CATEGORY_MAP.get(agent_name)
    if not cat:
        return None
    return PROMPTS_BASE / cat / f"{agent_name}.md"


@app.route("/api/params/agents")
def params_list_agents():
    """Lista todos os agentes com metadados para a tela de parametrização."""
    result = []
    for name, meta in AGENT_META.items():
        path = _prompt_path(name)
        prompt_len = len(path.read_text(encoding="utf-8")) if path and path.exists() else 0
        result.append({
            "id": name,
            "label": meta["label"],
            "category": meta["category"],
            "icon": meta["icon"],
            "prompt_chars": prompt_len,
        })
    return jsonify(result)


@app.route("/api/params/agents/<agent_name>")
def params_get_agent(agent_name):
    """Retorna o prompt atual de um agente."""
    if agent_name not in AGENT_META:
        return jsonify({"error": "Agente não encontrado"}), 404
    path = _prompt_path(agent_name)
    if not path or not path.exists():
        return jsonify({"error": "Arquivo de prompt não encontrado"}), 404
    return jsonify({
        "id": agent_name,
        **AGENT_META[agent_name],
        "prompt": path.read_text(encoding="utf-8"),
        "model": settings.model,
        "max_tokens": settings.max_tokens,
    })


@app.route("/api/params/agents/<agent_name>", methods=["PUT"])
def params_update_agent(agent_name):
    """Atualiza o prompt de um agente."""
    if agent_name not in AGENT_META:
        return jsonify({"error": "Agente não encontrado"}), 404
    path = _prompt_path(agent_name)
    if not path:
        return jsonify({"error": "Caminho de prompt inválido"}), 400

    data = request.json or {}
    new_prompt = data.get("prompt", "").strip()
    if not new_prompt:
        return jsonify({"error": "Prompt não pode ser vazio"}), 400

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_prompt, encoding="utf-8")

    # Recarrega o prompt no agente em memória
    agent = orchestrator.agents.get(agent_name)
    if agent:
        agent.system_prompt = new_prompt

    return jsonify({"ok": True, "chars": len(new_prompt)})


# ── Execução avulsa de agente único ──────────────────────────────────────────

@app.route("/api/agent/run", methods=["POST"])
def run_single_agent():
    """Executa um único agente com o contexto fornecido pelas perguntas."""
    data = request.json or {}
    agent_name = data.get("agent_name", "").strip()
    answers    = data.get("answers", {})      # dict { pergunta: resposta }

    if not agent_name:
        return jsonify({"error": "agent_name é obrigatório"}), 400
    if agent_name not in orchestrator.agents:
        return jsonify({"error": "Agente não encontrado"}), 404
    if not settings.has_anthropic():
        return jsonify({"error": "ANTHROPIC_API_KEY não configurada"}), 503

    # Monta a task a partir das respostas
    lines = ["## Contexto fornecido pelo usuário\n"]
    for q, a in answers.items():
        if a and str(a).strip():
            lines.append(f"**{q}:** {a}")
    task_text = "\n".join(lines)

    import uuid
    agent = orchestrator.agents[agent_name]
    execution = agent.execute(
        task=task_text,
        context={},
        task_id=uuid.uuid4(),
        phase_number=1
    )

    # Mensagem amigável se o erro for de crédito
    error_msg = execution.error_message
    if error_msg and ("credit balance" in error_msg.lower() or "billing" in error_msg.lower()):
        error_msg = "Saldo insuficiente na API Anthropic. Adicione créditos em console.anthropic.com/settings/billing"

    return jsonify({
        "status":        execution.status,
        "output":        execution.output_text,
        "tokens_input":  execution.tokens_input,
        "tokens_output": execution.tokens_output,
        "time_ms":       execution.execution_time_ms,
        "error":         error_msg,
    })


# ── Análise de documento para preenchimento automático do questionário ─────────

def _extract_text_from_file(file_storage) -> str:
    """Extrai texto de PDF ou DOCX."""
    filename = file_storage.filename.lower()
    data = file_storage.read()

    if filename.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n\n".join(pages)
        except Exception as e:
            raise ValueError(f"Erro ao processar PDF: {e}")

    elif filename.endswith(".docx"):
        try:
            import docx as docx_lib
            doc = docx_lib.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            raise ValueError(f"Erro ao processar DOCX: {e}")

    elif filename.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")

    else:
        raise ValueError("Formato não suportado. Use PDF, DOCX ou TXT.")


# Mapa de todos os campos do questionário Go-to-Market (completo)
COMPLETO_FIELDS = {
    "proj_nome":      "Nome do projeto ou empresa",
    "proj_seg":       "Segmento de mercado (SaaS, E-commerce, Saúde, Educação, Finanças, Entretenimento, RH, Marketplace, Outro)",
    "proj_tipo":      "Tipo de aplicação (Web App/SaaS, Mobile App, API+Backend, E-commerce, Dashboard/Analytics, Plataforma com IA)",
    "proj_desc":      "Descrição do produto em 2-3 frases: o que faz, para quem, qual problema resolve e diferencial",
    "proj_publico":   "Público-alvo principal: idade, perfil, cargo, comportamento, dores",
    "proj_escala":    "Escala esperada de usuários (Até 1.000 / 1K-50K / 50K-500K / 500K+)",
    "brand_tom":      "Tom e personalidade da marca (Profissional / Moderno e Inovador / Jovem e Dinâmico / Luxo e Premium / Minimalista / Divertido e Acessível)",
    "brand_valores":  "Valores da marca (Confiança, Inovação, Sustentabilidade, Performance, Humanidade, Segurança, Criatividade, Transparência, Exclusividade, Acessibilidade)",
    "ui_estilo":      "Estilo visual desejado (Dark/Moderno, Light/Clean, Bold e Colorido, Corporativo Clássico, Suave/Orgânico)",
    "brand_refs":     "Marcas e produtos que admira como referência visual",
    "ux_funcoes":     "Principais funcionalidades do produto (liste até 5)",
    "ux_devices":     "Dispositivos prioritários (Desktop, Mobile, Tablet)",
    "ux_complexidade":"Complexidade da interface (Simples 1-3 telas / Média 4-10 telas / Complexa 10+ telas)",
    "uw_idioma":      "Idioma principal do produto (Português BR, Inglês, Espanhol, Bilíngue, Multilíngue)",
    "uw_tom":         "Tom de voz da escrita (Formal e técnico / Amigável e casual / Consultivo / Energético e direto / Técnico mas acessível)",
    "ux_dores":       "Principais dores ou frustrações do usuário na solução atual",
    "tl_stack":       "Tecnologias já definidas ou preferências de stack (frameworks, linguagens, bancos)",
    "tl_prazo":       "Prazo estimado do projeto (MVP 4-6 semanas / 3 meses / 6 meses / 1 ano+ / Sem prazo)",
    "be_db":          "Banco de dados preferido (PostgreSQL, MySQL, MongoDB, Supabase, Firebase, Sem preferência)",
    "be_auth":        "Estratégia de autenticação (JWT, OAuth2, Magic Link, Supabase Auth, Sem preferência)",
    "tl_integr":      "Integrações necessárias (Pagamentos, Auth OAuth, Email, SMS/WhatsApp, Analytics, Storage, IA/LLMs)",
    "tl_segur":       "Requisitos de segurança ou compliance (LGPD, PCI-DSS, MFA, criptografia, SOC2)",
    "fe_framework":   "Framework frontend (React/Next.js, Vue/Nuxt, Angular, Svelte, Sem preferência)",
    "fe_ssr":         "SEO/SSR é importante? (Sim crítico / Não é interno / Híbrido)",
    "mob_plat":       "Plataformas mobile (iOS+Android, iOS apenas, Android apenas, PWA, Não tem mobile)",
    "mob_fw":         "Framework mobile (React Native+Expo, Flutter, Nativo, Sem preferência, Não se aplica)",
    "qa_tipos":       "Tipos de testes prioritários (unitários, integração, E2E, performance, segurança, smoke)",
    "qa_criticos":    "Fluxos críticos que nunca podem falhar",
    "do_cloud":       "Cloud provider (AWS, GCP, Azure, Vercel+Railway, DigitalOcean, Sem preferência)",
    "do_ci":          "CI/CD pipeline (GitHub Actions, GitLab CI, CircleCI, Sem CI/CD, Sem preferência)",
    "do_sla":         "SLA de disponibilidade esperado (99% / 99.9% / 99.99%)",
}


@app.route("/api/analyze-document", methods=["POST"])
def analyze_document():
    """
    Recebe um arquivo (PDF/DOCX) ou texto puro e usa Claude para
    mapear o conteúdo às perguntas do questionário Go-to-Market.
    Retorna { filled: {field_id: value}, missing: [field_id] }
    """
    if not settings.has_anthropic():
        return jsonify({"error": "ANTHROPIC_API_KEY não configurada"}), 503

    # Extrai texto
    raw_text = ""
    if "file" in request.files and request.files["file"].filename:
        try:
            raw_text = _extract_text_from_file(request.files["file"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        raw_text = (request.form.get("text") or "").strip()

    if not raw_text:
        return jsonify({"error": "Nenhum conteúdo recebido"}), 400

    # Monta lista de campos para o prompt
    fields_desc = "\n".join(
        f'- "{fid}": {desc}' for fid, desc in COMPLETO_FIELDS.items()
    )

    prompt = f"""Você é um assistente que analisa documentos de briefing de produto e extrai informações estruturadas.

Analise o documento abaixo e preencha SOMENTE os campos que encontrar resposta clara no texto.
Para campos de seleção, retorne exatamente uma das opções listadas.
Para campos de múltipla escolha, retorne os valores separados por vírgula.
Se não encontrar informação suficiente para um campo, NÃO inclua ele no JSON de resposta.

CAMPOS A PREENCHER:
{fields_desc}

DOCUMENTO:
---
{raw_text[:12000]}
---

Responda APENAS com um JSON válido no formato:
{{
  "filled": {{
    "field_id": "valor encontrado no documento",
    ...
  }}
}}

Não inclua explicações, apenas o JSON."""

    from anthropic import Anthropic, BadRequestError, APIStatusError
    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.create(
            model=settings.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
    except APIStatusError as api_err:
        msg = str(api_err)
        if "credit balance" in msg.lower() or "billing" in msg.lower():
            return jsonify({"error": "Saldo insuficiente na API Anthropic. Adicione créditos em console.anthropic.com/settings/billing"}), 402
        return jsonify({"error": f"Erro na API Anthropic: {msg}"}), 500

    raw_response = response.content[0].text.strip()

    # Extrai JSON da resposta
    try:
        # Remove possíveis blocos de código markdown
        if "```" in raw_response:
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        parsed = json.loads(raw_response)
        filled = parsed.get("filled", {})
    except Exception:
        return jsonify({"error": "Erro ao processar resposta da IA", "raw": raw_response}), 500

    # Campos que não foram preenchidos
    missing = [fid for fid in COMPLETO_FIELDS if fid not in filled]

    return jsonify({
        "filled":   filled,
        "missing":  missing,
        "total":    len(COMPLETO_FIELDS),
        "found":    len(filled),
    })


@app.route("/api/squads")
def list_squads():
    return jsonify(list(SQUADS.values()))


LOGOS_DIR = Path(__file__).parent / "static" / "logos"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

# Mapa em memória: project_id -> logo URL relativa
_project_logos: dict = {}


def _logo_url(project_id: str) -> str | None:
    filename = f"{project_id}.png"
    if (LOGOS_DIR / filename).exists():
        return f"/static/logos/{filename}"
    return None


@app.route("/static/logos/<path:filename>")
def serve_logo(filename):
    return send_from_directory(LOGOS_DIR, filename)


@app.route("/api/projects", methods=["GET"])
def list_projects():
    projects = db.list_projects()
    return jsonify([{
        "id": str(p.id),
        "name": p.name,
        "description": p.description or "",
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "logo": _logo_url(str(p.id)),
    } for p in projects])


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    logo_data_url = data.get("logo", "")        # "data:image/png;base64,..."

    if not name:
        return jsonify({"error": "Nome é obrigatório"}), 400

    project = db.create_project(name, description)
    project_id = str(project.id)

    # Salva logo se enviada
    logo_url = None
    if logo_data_url and logo_data_url.startswith("data:image"):
        try:
            header, b64 = logo_data_url.split(",", 1)
            img_bytes = base64.b64decode(b64)
            # Detecta extensão
            ext = "png"
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "webp" in header:
                ext = "webp"
            dest = LOGOS_DIR / f"{project_id}.{ext}"
            dest.write_bytes(img_bytes)
            logo_url = f"/static/logos/{project_id}.{ext}"
        except Exception as e:
            logger.warning(f"Falha ao salvar logo: {e}")

    return jsonify({
        "id": project_id,
        "name": project.name,
        "logo": logo_url,
    }), 201


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
