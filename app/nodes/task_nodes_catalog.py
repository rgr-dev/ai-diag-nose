import logging
import asyncio

from app.constants import Constants
from app.domain.state import State
from langgraph.types import Command

from app.nodes.utils import format_diagnosis_report_message

logger = logging.getLogger(__name__)


def dummy_node_a(state: State) -> Command:
    '''A dummy node that can be used for testing or as a placeholder in the workflow.'''
    return Command(update={'info_message': 'This is the dummy node A.'})

def dummy_node_b(state: State) -> Command:
    '''A dummy node that can be used for testing or as a placeholder in the workflow.'''
    return Command(update={'info_message': 'This is the dummy node B.'})


def dummy_node_c(state: State) -> Command:
    '''A dummy node that can be used for testing or as a placeholder in the workflow.'''
    return Command(update={'info_message': 'This is the dummy node C.'})

def query_logs_node(query_logs_fn):
    def node(state: State) -> Command:
        '''Tool node to query logs from Loki using the provided query in the context.
        This node will execute the Loki query specified in the context and return the resulting log entries.
        '''
        logs = query_logs_fn(state.context.logs_query)
        return Command(update={'error_logs': logs})
    return node
    

def git_fetch(state: State) -> Command:
    '''Tool node to fetch the latest code from the git repository specified in the context.
    This node will clone or pull the git repository associated with the service to ensure that we have the most up-to-date code for analysis.
    '''
    from app.scripts.git_scripts import git_clone_or_pull_repo
    success = git_clone_or_pull_repo(state.context.repository)
    if success:
        logger.info("Git fetch successful.")
        return Command(update={'info_message': 'Git fetch successful.'})
    else:
        logger.error("Git fetch failed.")
        # return Command(update={'info_message': 'Git fetch failed.'}, goto=END)
        return Command(update={'error_message': 'Git fetch failed.'})
    

def last_touched_files(state: State) -> Command:
    '''Tool node to get the list of files changed in the last commit.
    This node will analyze the git repository to identify which files were modified in the most recent commit, providing insights into what parts of the codebase may be relevant to the issues identified in the logs.
    '''
    from app.scripts.git_scripts import git_last_touched_files
    last_files = git_last_touched_files(state.context.service_name)
    return Command(update={'last_files_touched': last_files})


def load_service_info(state: State) -> Command:
    '''Tool node to load service information from the project repository.
    This node will read the README.md or other relevant files from the git repository to extract information about the service, such as its functionality, dependencies, and any other contextual information that may be useful for analysis.
    '''
    from app.scripts.service_reg import load_project_info_content
    service_info = load_project_info_content(state.context.service_name, state.context.description_file)
    return Command(update={'service_info': service_info})


def load_secrets(state: State) -> Command:
    '''Tool node to load secrets related to the service under analysis and its reference services.
    This node will retrieve any relevant secrets from AWS Secrets Manager or other secret management systems, providing necessary credentials or sensitive information that may be required for analysis and remediation.
    '''
    from app.skills.scripts.aws_secrets_scripts import get_aws_secrets
    secrets = get_aws_secrets(state.context.service_name)
    reference_services_secrets = {s: get_aws_secrets(s) for s in state.context.reference_services}
    return Command(update={'secrets_info': {'service_on_analysis_secrets': secrets, 'reference_service_secrets': reference_services_secrets}})


def skills_loader_node(state: State) -> Command:
    '''Tool node to load available skills from the skills directory.
    This node will scan the app/skills directory to identify and load all available skills, providing a catalog of tools and capabilities that can be utilized for analysis and remediation within the workflow.
    '''
    from app.scripts.skills_loader import load_skills
    skills = load_skills()
    return Command(update={'skills_catalog': skills})


def send_diagnosis_message(message_fn):
    def node(state: State) -> Command:
        '''
        Tool node to send the diagnosis message to a communication channel (e.g., Telegram) using the provided message sending function.
        '''
        logger.info("Sending diagnosis message to communication channel...")
        results = asyncio.run(message_fn(format_diagnosis_report_message(state), callback_data_prefix=f'{Constants.CALLBACK_DATA_PREFIX}{state.context.thread_id}'))
        if results and any(results.values()):
            logger.info("Diagnosis message sent successfully to at least one target.")
            return Command(update={'info_message': 'Diagnosis message sent successfully to at least one target.'})
        else:
            logger.error("Failed to send diagnosis message to any target.")
            return Command(update={'error_message': 'Failed to send diagnosis message to any target.'})
    return node

def send_simple_message(message_fn):
    def node(state: State) -> Command:
        '''
        Tool node to send a simple message to a communication channel (e.g., Telegram) using the provided message sending function.
        '''
        logger.info("Sending message to communication channel...")
        results = asyncio.run(message_fn(state.final_message))
        if results and any(results.values()):
            logger.info("Message sent successfully to at least one target.")
            return Command(update={'info_message': 'Message sent successfully to at least one target.'})
        else:
            logger.error("Failed to send message to any target.")
            return Command(update={'error_message': 'Failed to send message to any target.'})
    return node