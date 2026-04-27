

import os
import psycopg2
import logging


logger = logging.getLogger(__name__)


def database_scripts_executor(query):
    """
    Executes a database query using connection parameters from environment variables.
    
    Environment Variables:
        DB_HOST (str): Database host address
        DB_PORT (int): Database port number
        DB_USER (str): Database username
        DB_PASSWORD (str): Database password
        DB_NAME (str): Database name
    Args:
        query (str): SQL query to execute
    Returns:
        list: Query results or None if execution fails
    """
    try:
        # For PostgreSQL
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            dbname=os.environ["DB_NAME"]
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Error executing query: %s", e)
        return None


