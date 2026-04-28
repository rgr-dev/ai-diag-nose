import re
import logging
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import ContextTypes
from app.constants import Constants
from app.domain.state import ContextSchema
from app.graph.workflow import build_workflow

from langgraph.types import Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore 

import asyncio
from app.scripts.db_connection import get_db_uri
from app.scripts.t_bot import listen_for_confirmation, send_confirmation_message


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
)
logger = logging.getLogger(__name__)


load_dotenv()


async def resume_workflow(user_desicion: str, thread_id: str):
    database_uri = get_db_uri()
    async with (
        AsyncPostgresStore.from_conn_string(database_uri) as store,
        AsyncPostgresSaver.from_conn_string(database_uri) as checkpointer,
    ):
        await store.setup()
        await checkpointer.setup()
        chain = build_workflow(checkpointer=checkpointer, store=store, generate_graph=True)
        config = {"configurable": {"thread_id": thread_id}}
        final_state = await chain.ainvoke(Command(resume=user_desicion), config)
        logger.info('-------------------')
        logger.info(final_state)

                
async def continue_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logger.info(f"Received callback query: {query.data if query else 'None'}")
    if query is None or not query.data or not query.data.startswith(Constants.CALLBACK_DATA_PREFIX):
        return

    await query.answer()
    query_data = query.data
    
    user_desicion = query_data.split(":")[-1]  # Extract the user desicion 
    thread_id = query_data.split(":")[1]  # Extract the service key from callback data

    logger.info(f"Received user decision: {user_desicion} for thread_id: {thread_id}")
    
    if user_desicion == Constants.HUMAN_ADVICE:
        logger.info(f"Waiting for user advice input for {thread_id}.")
        await update.effective_message.reply_text(
                f'[tid:{thread_id}] Por favor, indícame cómo continuar.',
                reply_markup=ForceReply(selective=True)
            )
    await resume_workflow(user_desicion=user_desicion, thread_id=thread_id)



async def handle_reply_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.reply_to_message or msg.reply_to_message.from_user.id != context.bot.id:
        return

    text = msg.reply_to_message.text or ""
    match = re.search(r"\[tid:(.*?)\]", text)
    if not match:
        return

    thread_id = match.group(1)
    user_input = msg.text
    
    await msg.reply_text(f"Perfecto, gracias por tu aporte. Estoy procesando tu sugerencia para el thread id <b>{thread_id}</b>.", parse_mode="HTML")
    await resume_workflow(user_desicion=user_input, thread_id=thread_id)


# Example Received callback query: diagnosis_report:diagnosis-service-b-74692c80:approved
while True:
    asyncio.run(listen_for_confirmation(
        callback_data_prefix=Constants.CALLBACK_DATA_PREFIX,
        custom_message_handler=handle_reply_advice,
        custom_callback_handler=continue_workflow,
        timeout=30))
    asyncio.sleep(5)