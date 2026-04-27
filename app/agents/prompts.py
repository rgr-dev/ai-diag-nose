from textwrap import dedent
from string import Template


def get_bound_message(prompt_template_raw: str, entries: dict) -> str:
    prompt_template = Template(dedent(prompt_template_raw))
    return prompt_template.substitute(entries)


SERVICE_INFO_PREFIX_PROMPT = """
    ## Issue related context information:
    ### Service Name: 
    - ${service_name}
    
    ### Operational info:
    ${service_info}
    
    ###Last Touched Files (on git):
    ${last_files_touched}
    
    ### Error Logs:
    ```
    ${error_logs}
    ```
    """

SERVICE_INFO_PREFIX_PROMPT = """
    ## Issue related context information:
    ### Service Name: 
    - ${service_name}
    
    ###Last Touched Files (on git):
    ${last_files_touched}
    
    ### Error Logs:
    ```
    ${error_logs}
    ```
    """

REMEDIATION_AGENT_SYSTEM_PROMPT = [
    "You are the DevOps engineer responsible for diagnosing and resolving issues in a software service. "
    "Based on the provided context generated from a diagnosis & remediation flow, your task is to execute the remediation steps to resolve the issue."
    ]

REMEDIATION_AGENT_ACTION_PROMPT = """
    ### Context:
    ${context}
    
    ### Secrets comparison:
    - Service secrets: ${service_on_analysis_secrets}
    - Reference services secrets: ${reference_service_secrets}
    
    ### Previous remediation steps suggestion (takes this as a reference):
    <previous_suggestion>
    ${remediation_suggestion}
    </previous_suggestion>

    ---
    ### Guidelines:
    - Use the tools at your disposal to gather information (if needed) and reach the solution.
    - Always refer to the provided context and any additional information you have gathered during the process.
    - Pay attention to tools descriptions and use them effectively to achieve the best results.
    
    So, go ahead and fix the error in the service executing the recomended tool or tools in the most efficient way possible.
    """