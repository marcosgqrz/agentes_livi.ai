"""
Deployer: extrai código dos outputs dos agentes e cria um build estático local.
Retorna uma URL servida pelo próprio Flask em /static/builds/<run_id>/
"""
import re
from pathlib import Path

BUILDS_DIR = Path(__file__).parent.parent / "web" / "static" / "builds"

AGENT_LABELS = {
    "brand_designer": "Brand Designer",
    "ux_designer": "UX Designer",
    "ui_designer": "UI Designer",
    "ux_writer": "UX Writer",
    "tech_lead": "Tech Lead",
    "frontend_dev": "Frontend Dev",
    "backend_dev": "Backend Dev",
    "mobile_dev": "Mobile Dev",
    "qa_engineer": "QA Engineer",
    "devops_engineer": "DevOps Engineer",
}

AGENT_ICONS = {
    "brand_designer": "🎯",
    "ux_designer": "🗺️",
    "ui_designer": "🎨",
    "ux_writer": "✍️",
    "tech_lead": "🏗️",
    "frontend_dev": "💻",
    "backend_dev": "⚙️",
    "mobile_dev": "📱",
    "qa_engineer": "🧪",
    "devops_engineer": "🚀",
}


def _extract_code_blocks(text: str, lang: str) -> list[str]:
    pattern = rf"```{lang}\s*\n(.*?)```"
    return re.findall(pattern, text, re.DOTALL | re.IGNORECASE)


def _find_html(agent_outputs: dict) -> str | None:
    """Procura o maior bloco HTML nos outputs (prioriza frontend_dev)."""
    candidates = []
    for agent in ["frontend_dev", "ui_designer", "ux_designer"]:
        output = agent_outputs.get(agent, "")
        blocks = _extract_code_blocks(output, "html")
        candidates.extend(blocks)
    if candidates:
        return max(candidates, key=len)
    return None


def _generate_summary_page(run_id: str, agent_outputs: dict) -> str:
    """Gera página HTML elegante com todos os outputs renderizados como Markdown."""
    sections_html = ""
    order = [
        "brand_designer", "ux_designer", "ux_writer", "ui_designer",
        "tech_lead", "frontend_dev", "backend_dev", "mobile_dev",
        "qa_engineer", "devops_engineer",
    ]
    agents_in_order = [a for a in order if a in agent_outputs]
    for a in agent_outputs:
        if a not in agents_in_order:
            agents_in_order.append(a)

    for agent in agents_in_order:
        label = AGENT_LABELS.get(agent, agent.replace("_", " ").title())
        icon = AGENT_ICONS.get(agent, "🤖")
        content = agent_outputs[agent].replace("`", "&#96;").replace("\\", "\\\\")
        sections_html += f"""
        <section class="agent-section" id="{agent}">
          <div class="agent-header">
            <span class="agent-icon">{icon}</span>
            <h2>{label}</h2>
          </div>
          <div class="agent-body markdown" data-md="{agent}"></div>
        </section>
        """

    # Gera JS com os conteúdos (escapado para JSON)
    import json
    contents_json = json.dumps({
        a: agent_outputs[a] for a in agents_in_order
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Entregável — Agent Orchestrator</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    line-height: 1.7;
  }}
  header {{
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid #334155;
    padding: 2rem;
    text-align: center;
  }}
  header h1 {{ font-size: 2rem; color: #f8fafc; font-weight: 700; }}
  header p {{ color: #94a3b8; margin-top: 0.5rem; }}
  .badge {{
    display: inline-block;
    background: #6366f1;
    color: white;
    font-size: 0.75rem;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    margin-top: 0.75rem;
    font-weight: 600;
  }}
  nav {{
    position: sticky;
    top: 0;
    background: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 0.75rem 2rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    z-index: 100;
  }}
  nav a {{
    color: #94a3b8;
    text-decoration: none;
    font-size: 0.8rem;
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    border: 1px solid #334155;
    transition: all 0.2s;
  }}
  nav a:hover {{ background: #334155; color: #f1f5f9; }}
  main {{ max-width: 960px; margin: 0 auto; padding: 2rem; }}
  .agent-section {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    margin-bottom: 2rem;
    overflow: hidden;
  }}
  .agent-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    background: #0f172a;
    border-bottom: 1px solid #334155;
  }}
  .agent-icon {{ font-size: 1.5rem; }}
  .agent-header h2 {{ font-size: 1.1rem; font-weight: 600; color: #f1f5f9; }}
  .agent-body {{ padding: 1.5rem; }}
  /* Markdown styles */
  .agent-body h1, .agent-body h2, .agent-body h3 {{
    color: #f1f5f9; margin-top: 1.5rem; margin-bottom: 0.5rem;
  }}
  .agent-body h1 {{ font-size: 1.4rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
  .agent-body h2 {{ font-size: 1.15rem; }}
  .agent-body h3 {{ font-size: 1rem; color: #94a3b8; }}
  .agent-body p {{ color: #cbd5e1; margin-bottom: 0.75rem; }}
  .agent-body ul, .agent-body ol {{ padding-left: 1.5rem; color: #cbd5e1; margin-bottom: 0.75rem; }}
  .agent-body li {{ margin-bottom: 0.25rem; }}
  .agent-body code {{
    background: #0f172a; color: #a5f3fc;
    padding: 0.15rem 0.4rem; border-radius: 4px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.85em;
  }}
  .agent-body pre {{
    background: #0f172a; border: 1px solid #334155;
    border-radius: 8px; padding: 1rem; overflow-x: auto;
    margin-bottom: 1rem;
  }}
  .agent-body pre code {{ background: none; padding: 0; color: #e2e8f0; }}
  .agent-body strong {{ color: #f1f5f9; }}
  .agent-body blockquote {{
    border-left: 3px solid #6366f1; padding-left: 1rem;
    color: #94a3b8; margin: 1rem 0;
  }}
  .agent-body table {{
    width: 100%; border-collapse: collapse; margin-bottom: 1rem;
  }}
  .agent-body th, .agent-body td {{
    border: 1px solid #334155; padding: 0.5rem 0.75rem; text-align: left;
  }}
  .agent-body th {{ background: #0f172a; color: #f1f5f9; }}
  footer {{
    text-align: center; padding: 2rem; color: #475569; font-size: 0.85rem;
    border-top: 1px solid #1e293b;
  }}
</style>
</head>
<body>
<header>
  <h1>🤖 Entregável do Projeto</h1>
  <p>Gerado pelo Agent Orchestrator com {len(agent_outputs)} agentes especializados</p>
  <span class="badge">Run ID: {run_id[:8]}...</span>
</header>
<nav>
  {''.join(f'<a href="#{a}">{AGENT_ICONS.get(a,"🤖")} {AGENT_LABELS.get(a, a)}</a>' for a in agents_in_order)}
</nav>
<main>
  {sections_html}
</main>
<footer>
  Gerado por Agent Orchestrator &mdash; {len(agent_outputs)} agentes &mdash; claude-sonnet-4-6
</footer>
<script>
const CONTENTS = {contents_json};
document.querySelectorAll('.markdown[data-md]').forEach(el => {{
  const agent = el.getAttribute('data-md');
  if (CONTENTS[agent]) {{
    el.innerHTML = marked.parse(CONTENTS[agent]);
  }}
}});
</script>
</body>
</html>"""


def deploy_build(run_id: str, agent_outputs: dict, base_url: str = "http://localhost:5000") -> str:
    """
    Cria build estático dos outputs e retorna a URL local.
    Prioriza HTML gerado pelo frontend_dev; se não encontrar, gera página de sumário.
    """
    BUILDS_DIR.mkdir(parents=True, exist_ok=True)
    build_dir = BUILDS_DIR / run_id
    build_dir.mkdir(exist_ok=True)

    html = _find_html(agent_outputs)
    if html:
        (build_dir / "index.html").write_text(html, encoding="utf-8")
        source = "frontend_code"
    else:
        summary = _generate_summary_page(run_id, agent_outputs)
        (build_dir / "index.html").write_text(summary, encoding="utf-8")
        source = "summary"

    url = f"{base_url}/static/builds/{run_id}/"
    return url, source
