import os


def get_db_uri():
    """
    Constructs the database URI from environment variables.
    Defaults to localhost and standard PostgreSQL settings if not provided.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "agents_workflow")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"