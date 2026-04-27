from langchain import tools
from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph

from app.agents.llm_factory import LLMsFactory
from app.agents.prompts import REMEDIATION_AGENT_SYSTEM_PROMPT
from app.domain.state import State
from app.graph.middlewares import log_response, select_tools, add_context
from app.nodes.agents_catalog import *
from app.nodes.edges_catalog import *
from app.nodes.hitl_interruptors import *
from app.nodes.task_nodes_catalog import *
from app.scripts.logs import query_logs
from app.scripts.t_bot import *
from app.scripts.tools_loader import load_tools_from_skills


def build_workflow(checkpointer=None, store=None, generate_graph: bool = False) -> StateGraph:

    # llm instances
    llms_factory = LLMsFactory()
    # diagnosis_llm = llms_factory.ollama
    openai_llm = llms_factory.openai
    
    # agents (with node wrappers and middlewares)
    remediation_executor_agent = create_agent(
        openai_llm,
        middleware=[select_tools, add_context, log_response],
        tools=load_tools_from_skills(),
        system_prompt=REMEDIATION_AGENT_SYSTEM_PROMPT,
        state_schema=State)
    remediation_agent_executor_n = remediation_agent_executor_node(remediation_executor_agent)

    # nodes (injecting deps)
    query_logs_task = query_logs_node(query_logs)
    send_diagnosis_message_task = send_diagnosis_message(send_confirmation_message)
    diagnosis_llm = diagnosis_node(openai_llm)
    diagnosis_check_llm = diagnosis_check_node(openai_llm)
    remediation_llm = remediation_node(openai_llm)
    skills_suggestion_llm = skills_suggestion_node(openai_llm)
    human_advice_processor_llm = human_advice_processor_node(openai_llm)
    

    workflow = StateGraph(State)
    
    # Nodes represent the individual steps or actions in the workflow. Each node is associated with a specific function that performs a task.    
    workflow.add_node('query_logs_task', query_logs_task)
    workflow.add_node('git_fetch_task', git_fetch)
    workflow.add_node('last_touched_files_task', last_touched_files)
    workflow.add_node('load_service_info_task', load_service_info)
    workflow.add_node('secrets_retriever_task', load_secrets)
    workflow.add_node('diagnosis_llm', diagnosis_llm)
    workflow.add_node('diagnosis_check_llm', diagnosis_check_llm)
    workflow.add_node('skills_loader_task', skills_loader_node)
    workflow.add_node('skills_suggestion_llm', skills_suggestion_llm)
    workflow.add_node('remediation_llm', remediation_llm)
    workflow.add_node('human_advice_processor_llm', human_advice_processor_llm)
    workflow.add_node('send_diagnosis_message_task', send_diagnosis_message_task)
    workflow.add_node('remediation_executor_agent', remediation_executor_agent)
    workflow.add_node('approval_hitl', human_approval_node)
    workflow.add_node('get_advice_hitl', human_advice_node)
    workflow.add_node('dummy_node_a', dummy_node_a)
    workflow.add_node('dummy_node_b', dummy_node_b)
    workflow.add_node('dummy_node_c', dummy_node_c)
    
    # Edges (and conditional edges) define the flow of the graph, connecting the start to the first node, and then to the end.
    workflow.add_edge(START, 'query_logs_task')
    workflow.add_conditional_edges('query_logs_task', check_logs_router, {'error': 'git_fetch_task', 'clean': END})
    workflow.add_edge('git_fetch_task', 'last_touched_files_task')
    workflow.add_edge('last_touched_files_task', 'load_service_info_task')
    workflow.add_edge('load_service_info_task', 'secrets_retriever_task')
    workflow.add_edge('secrets_retriever_task', 'diagnosis_llm')
    workflow.add_edge('diagnosis_llm', 'diagnosis_check_llm')
    workflow.add_conditional_edges('diagnosis_check_llm', check_analysis_router, 
                                   {'proceed': 'skills_loader_task', 'moreInfo': 'dummy_node_a'})
    workflow.add_edge('skills_loader_task', 'skills_suggestion_llm')
    workflow.add_edge('skills_suggestion_llm', 'remediation_llm')
    workflow.add_edge('remediation_llm', 'send_diagnosis_message_task')
    workflow.add_edge('send_diagnosis_message_task', 'approval_hitl')
    workflow.add_conditional_edges('approval_hitl', check_human_approval_router, {
        Constants.HUMAN_APPROVE: 'remediation_executor_agent', Constants.HUMAN_REJECT: 'dummy_node_b', Constants.HUMAN_ADVICE: 'get_advice_hitl' })
    workflow.add_edge('get_advice_hitl', 'human_advice_processor_llm')
    workflow.add_conditional_edges('human_advice_processor_llm', check_human_advice_router, 
                                   {Constants.HUMAN_APPROVE: 'dummy_node_a', Constants.HUMAN_REJECT: 'dummy_node_b'})
    workflow.add_edge('remediation_executor_agent', 'dummy_node_c')
    workflow.add_edge('dummy_node_a', END)
    workflow.add_edge('dummy_node_b', END)
    workflow.add_edge('dummy_node_c', END)
    
    chain = workflow.compile(checkpointer=checkpointer, store=store)
    # chain = workflow.compile(checkpointer=checkpointer)
    if generate_graph:
        graph = chain.get_graph(xray=True)
        graph.draw_mermaid_png(output_file_path='workflow_graph.png')

    return chain