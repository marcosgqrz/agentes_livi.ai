from typing import Optional


TASK_TYPE_KEYWORDS = {
    "landing_page": ["landing page", "landing", "página de captura"],
    "website": ["website", "site", "portal"],
    "webapp": ["webapp", "web app", "aplicação web", "sistema web"],
    "mvp": ["mvp", "produto mínimo", "protótipo funcional"],
    "mobile_app": ["app mobile", "aplicativo", "app ios", "app android"],
    "ios_app": ["ios", "iphone", "ipad"],
    "android_app": ["android"],
    "branding": ["branding", "marca", "identidade visual", "logo"],
    "design_system": ["design system", "sistema de design"],
    "prototipo": ["protótipo", "wireframe", "mockup"],
    "implementacao": ["implementar", "desenvolver", "codar", "programar"],
    "codigo": ["código", "code", "script"],
    "feature": ["feature", "funcionalidade", "recurso"],
    "integracao": ["integração", "api", "webhook"],
    "componente": ["componente", "component"],
    "tela": ["tela", "screen", "página"],
    "modal": ["modal", "dialog", "popup"],
    "formulario": ["formulário", "form"],
}


def classify_task(task_input: str) -> str:
    """Classifica o tipo de tarefa baseado em palavras-chave."""
    task_lower = task_input.lower()

    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in task_lower:
                return task_type

    # Default: full_product
    return "landing_page"
