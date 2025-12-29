from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
from config import load_config


_engine: Engine | None = None


def _build_connection_url(config: dict) -> str:
    """
    Build an ODBC connection string that works with named instances and ports.
    Example server inputs:
    - localhost
    - localhost\\MSSQLSERVER01
    - localhost\\MSSQLSERVER01,56539
    - 127.0.0.1
    """
    server = config["server"]
    port = config.get("port")
    if port:
        # Append port if not already specified in server string
        if "," not in server:
            server = f"{server},{port}"
    driver = config["driver"]
    # TrustServerCertificate avoids TLS validation issues on dev boxes; adjust as needed.
    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};PWD={config['password']};"
        f"TrustServerCertificate=yes"
    )
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"


def get_engine() -> Engine:
    """
    Lazily create a pooled SQLAlchemy engine for SQL Server.
    """
    global _engine
    if _engine is None:
        cfg = load_config()
        pool_cfg = cfg["pool"]
        _engine = create_engine(
            _build_connection_url(cfg),
            pool_size=pool_cfg["max_size"],
            max_overflow=0,
            pool_timeout=pool_cfg["connection_timeout_ms"] / 1000,
            pool_recycle=pool_cfg["max_lifetime_ms"] / 1000,
            pool_pre_ping=True,
        )
    return _engine


def execute(query: str, params: dict | None = None):
    """
    Helper for one-off parameterized executions.
    """
    with get_engine().connect() as conn:
        return conn.execute(text(query), params or {})
