from app.agents.prompts import get_bound_message, SERVICE_INFO_PREFIX_PROMPT
from app.domain.state import State


def get_value(obj, key):
    if isinstance(obj, dict):
        return obj[key]
    return getattr(obj, key)


DIAGNOSIS_REPORT_CHAT_MESSAGE_PREFIX = """
<b>Attention!</b>\nThere are an error in the service ${service_name}.\n
Next, you can find some context information related to the issue:
    - <b>Relevant error logs:</b> <pre>${error_logs}</pre>
    - <b>Last touched files:</b> ${last_files_touched}\n
<b>How to solve:</b>\n${how_to_resolve}
"""

def format_diagnosis_report_message(state: State) -> str:
    chat_message = get_bound_message(DIAGNOSIS_REPORT_CHAT_MESSAGE_PREFIX,
                         {'service_name': state.context.service_name,
                          'last_files_touched': ', '.join(state.last_files_touched),
                          'error_logs': ', '.join(state.error_logs),
                          'how_to_resolve': state.remediation_steps_suggestion})
    return chat_message


def get_prompt_subfix(state: State) -> str:
    context = get_value(state, "context")
    return get_bound_message(
        SERVICE_INFO_PREFIX_PROMPT,
        {
            "service_name": get_value(context, "service_name"),
            "service_info": get_value(state, "service_info"),
            "last_files_touched": ", ".join(get_value(state, "last_files_touched")),
            "error_logs": ", ".join(get_value(state, "error_logs")),
        },
    )

def get_prompt_subfix_lite(state: State) -> str:
    context = get_value(state, "context")
    return get_bound_message(
        SERVICE_INFO_PREFIX_PROMPT,
        {
            "service_name": get_value(context, "service_name"),
            "last_files_touched": ", ".join(get_value(state, "last_files_touched")),
            "error_logs": ", ".join(get_value(state, "error_logs")),
        },
    )