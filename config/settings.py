import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-20250514"
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


settings = Settings()
