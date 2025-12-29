import os
from pathlib import Path
from dotenv import load_dotenv


def load_config(env_path: Path | None = None) -> dict:
    """
    Load environment configuration for database/pool settings.
    Defaults to .env in project root.
    """
    env_file = env_path or Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    return {
        "server": os.getenv("DB_SERVER", "localhost"),
        "port": int(os.getenv("DB_PORT", "1433")),
        "database": os.getenv("DB_NAME", "BankDB"),
        "user": os.getenv("DB_USER", "sa"),
        "password": os.getenv("DB_PASSWORD", ""),
        "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
        "pool": {
            "max_size": int(os.getenv("POOL_MAX_SIZE", "10")),
            "min_idle": int(os.getenv("POOL_MIN_IDLE", "2")),
            "idle_timeout_ms": int(os.getenv("POOL_IDLE_TIMEOUT_MS", "300000")),
            "max_lifetime_ms": int(os.getenv("POOL_MAX_LIFETIME_MS", "1800000")),
            "connection_timeout_ms": int(os.getenv("POOL_CONNECTION_TIMEOUT_MS", "10000")),
        },
    }
