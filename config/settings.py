import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

import pathlib
load_dotenv(pathlib.Path(__file__).parent.parent / ".env", override=True)


@dataclass
class Settings:
    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096

    # Supabase
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))

    # Execução
    max_parallel_agents: int = 3
    default_timeout_seconds: int = 120
    retry_attempts: int = 2

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate(self) -> bool:
        """Valida se todas as configurações obrigatórias estão presentes."""
        required = [self.anthropic_api_key, self.supabase_url, self.supabase_key]
        return all(required)

    def has_anthropic(self) -> bool:
        """Verifica se a chave da Anthropic está presente (necessária para executar agentes)."""
        return bool(self.anthropic_api_key)

    def has_supabase(self) -> bool:
        """Verifica se as credenciais do Supabase estão presentes."""
        return bool(self.supabase_url and self.supabase_key)

    @property
    def dev_mode(self) -> bool:
        """True quando o Supabase não está configurado (dados ficam em memória)."""
        return not self.has_supabase()


settings = Settings()
