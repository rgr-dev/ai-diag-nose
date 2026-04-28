import logging

from langchain.agents.middleware import AgentState, after_agent, wrap_model_call, ModelRequest, ModelResponse
from langgraph.runtime import Runtime
from typing import Any, Callable

from langchain.messages import SystemMessage

from app.agents.prompts import REMEDIATION_AGENT_ACTION_PROMPT, get_bound_message
from app.nodes.utils import get_prompt_subfix_lite
from app.scripts.tools_loader import load_tools

logger = logging.getLogger(__name__)


def _get_tools_list_from_state(state) -> str:
    return [
        script
        for skill in state["skills_suggestion"]
        for script in state["skills_catalog"][skill.name]["scripts"]
    ]


@wrap_model_call
async def select_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Middleware to select relevant tools based on state/context."""
    advice_tools = []
    state_tools = load_tools(_get_tools_list_from_state(request.state))
    if request.state["human_advice_curated"]:
        advice_tools = load_tools(request.state["human_advice_curated"].tools)
    relevant_tools = [*state_tools, *advice_tools] 
    return await handler(request.override(tools=relevant_tools))


@wrap_model_call
async def add_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    tools = _get_tools_list_from_state(request.state)
    tools_to_use = f"{', '.join(tools)}"
    user_advice = request.state["human_advice_curated"].suggestions
    prompt_complement = get_bound_message(REMEDIATION_AGENT_ACTION_PROMPT, 
                                          {'context': get_prompt_subfix_lite(request.state), 
                                           'remediation_suggestion': request.state['remediation_steps_suggestion'],
                                           'service_on_analysis_secrets': request.state['secrets_info'].service_on_analysis_secrets,
                                           'reference_service_secrets': request.state['secrets_info'].reference_service_secrets,
                                           'human_chat_advice': user_advice})
    logger.debug(f"Adding context to system prompt. Tools: {tools_to_use}. Prompt complement: {prompt_complement}")
    new_content = list(request.system_message.content_blocks) + [
        {"type": "text", "text": f"you have access to the following tools: ."},
        {"type": "text", "text": tools_to_use},
        {"type": "text", "text": prompt_complement}
    ]
    new_system_message = SystemMessage(content=new_content)
    return await handler(request.override(system_message=new_system_message))

@after_agent
async def log_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    logger.info(f"Model returned: {state['messages'][-1].content}")
    return None