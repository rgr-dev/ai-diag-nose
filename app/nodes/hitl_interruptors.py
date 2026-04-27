import logging

from app.domain.state import State
from langgraph.types import Command, interrupt

logger = logging.getLogger(__name__)

def human_approval_node(state: State) -> Command:
    '''Pauses the workflow until a human approves or rejects the remediation.'''
    decision = interrupt({
        "message": "Approve or reject the remediation.",
        "diagnosis": state.final_message
    })
    return Command(update={"human_approval": decision})


def human_advice_node(state: State) -> Command:
    '''Pauses the workflow until a human provides advice.'''
    decision = interrupt({
        "message": "Provide your advice.",
        "diagnosis": state.final_message
    })
    return Command(update={"human_chat_advice": decision})