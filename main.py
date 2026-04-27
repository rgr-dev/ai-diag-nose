import asyncio
import logging
from pprint import pformat
import uuid
from dotenv import load_dotenv
from app.constants import Constants
from app.domain.state import ContextSchema
from app.graph.workflow import build_workflow
from app.scripts.db_connection import get_db_uri
from app.scripts.service_reg import load_services_dict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore 


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
)
logger = logging.getLogger(__name__)


load_dotenv()


async def run_workflow():
    database_uri = get_db_uri()
    async with (
        AsyncPostgresStore.from_conn_string(database_uri) as store,
        AsyncPostgresSaver.from_conn_string(database_uri) as checkpointer,
    ):
        await store.setup()
        await checkpointer.setup()
        services = load_services_dict('services-manifest.yml')
        chain = build_workflow(checkpointer=checkpointer, store=store, generate_graph=True)
        # chain = build_workflow(checkpointer=checkpointer, generate_graph=True)
        
        logger.info(services)
        for key, service_registry in services.items():
            service_registry = services[key]
            thread_id = f"{Constants.WORKFLOW_THREAD_ID_PREFIX}{key}-{uuid.uuid4().hex[:8]}"
            config = {"configurable": {"thread_id": thread_id}}
            context = ContextSchema(
                thread_id=thread_id,
                service_name=key,
                repository=service_registry.get('repository', ''),
                service_endpoint=service_registry.get('service_endpoint', ''),
                troubleshooting_file=service_registry.get('troubleshooting_file', 'troubleshooting-skill.md'),
                logs_query=service_registry.get('logs_query', ''),
                description_file=service_registry.get('description_file', 'README.md'),
                reference_services=service_registry.get('reference_services', []),
                service_dependencies=service_registry.get('service_dependencies', []),
            )
            state = await chain.ainvoke({'context': context}, config=config)
            logger.info('-------------------')
            logger.info("%s", pformat(state))

asyncio.run(run_workflow())