import logging

from app.constants import Constants
from app.domain import state
from app.domain.state import State

logger = logging.getLogger(__name__)



def check_logs_router(state: State) -> str:
    '''Tool node to check the retrieved logs for errors.
    This node will analyze the error logs retrieved from Loki and determine if there are any critical issues that need to be addressed.
    '''
    return 'error' if state.error_logs else 'clean'


def check_analysis_router(state: State) -> str:
    '''Tool node to check the analysis results for errors.
    This node will analyze the analysis results and determine if there are any critical issues that need to be addressed.
    '''
    return 'proceed' if state.analysis_check_result.proceed else 'moreInfo'


def check_human_approval_router(state: State) -> str:
    return state.human_approval

def check_human_advice_router(state: State) -> str:
    return state.human_advice_curated.decision if state.human_advice_curated.decision else Constants.HUMAN_REJECT