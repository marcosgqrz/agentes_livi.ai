from setuptools import setup, find_packages

setup(
    name="agent-orchestrator",
    version="1.0.0",
    description="Orquestrador Multi-Agente para Equipe de Produto Digital",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.18.0",
        "supabase>=2.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "agent-orchestrator=main:main",
        ],
    },
)
