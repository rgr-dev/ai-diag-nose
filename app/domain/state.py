from pydantic import BaseModel, Field
from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass(frozen=True)
class ContextSchema(BaseModel):
    thread_id: str = ''
    service_name: str = ''
    repository: str = ''
    service_endpoint: str = ''
    logs_query: str = ''
    description_file: str = ''
    troubleshooting_file: str = ''
    reference_services: List[str] = Field(default_factory=list)
    service_dependencies: List[str] = Field(default_factory=list)


class HumanAdvicePayload(BaseModel):
    decision: str
    tools: List[str] = Field(default_factory=list)
    suggestions: str = ''
    confidence: float


class SkillSuggestion(BaseModel):
    name: str = ''
    description: str = ''
    justification: str = ''


class ThoughtsPayload(BaseModel):
    text: str = ''
    reasoning: str = ''
    plan: str = ''
    criticism: str = ''
    speak: str = ''


class CommandPayload(BaseModel):
    name: str = ''
    args: Dict[str, Any] = Field(default_factory=dict)


class ToolDecisionPayload(BaseModel):
    thoughts: ThoughtsPayload = ThoughtsPayload()
    command: CommandPayload = CommandPayload()


class CheckResult(BaseModel):
    justification: str
    proceed: bool

class SecretsInfo(BaseModel):
    service_on_analysis_secrets: Dict[str, str] = Field(default_factory=dict)
    reference_service_secrets: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class State(BaseModel):
    context: ContextSchema
    error_logs: List[str] = Field(default_factory=list)
    last_files_touched: List[str] = Field(default_factory=list)
    service_info: str = ''
    analysis_result: str = ''
    analysis_check_result: CheckResult = CheckResult(justification='', proceed=False)
    skills_catalog: Dict[str, Dict] = Field(default_factory=dict)
    skills_suggestion: List[SkillSuggestion] = Field(default_factory=list)
    info_message: str = ''
    secrets_info: SecretsInfo = SecretsInfo()
    remediation_steps_suggestion: str = ''
    human_approval: str = ''
    human_chat_advice: str = '' ## check if still needed
    human_advice_curated: HumanAdvicePayload = HumanAdvicePayload(decision='', tools=[], confidence=0.0)
    tool_decision: ToolDecisionPayload = ToolDecisionPayload()
    final_message: str = ''
    error_message: str = ''