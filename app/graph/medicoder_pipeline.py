"""
    author: @abhiyanhaze
    Description: Workflow using langgraph
"""

from langgraph.graph import END, START, StateGraph
from app.graph.states import MedicoderState
from app.graph.nodes import (
    input_handler_node,
    clinical_note_parser_node,
    condition_extractor_node,
    hcc_relevance_checker_node,
)


def _build_graph():
    graph = StateGraph(MedicoderState)

    graph.add_node("input_handler", input_handler_node)
    graph.add_node("parser", clinical_note_parser_node)
    graph.add_node("extractor", condition_extractor_node)
    graph.add_node("evaluator", hcc_relevance_checker_node)

    graph.add_edge(START, "input_handler")
    graph.add_edge("input_handler", "parser")
    graph.add_edge("parser", "extractor")
    graph.add_edge("extractor", "evaluator")
    graph.add_edge("evaluator", END)

    return graph


_graph = _build_graph().compile()

# Public handle used by `langgraph dev` (referenced in langgraph.json)
graph = _graph


def run(raw_input: str) -> list[dict]:
    """
    Run the medicoder pipeline.
    raw_input can be a file path or raw clinical note text.
    Returns a list of conditions annotated with hcc_relevant flag.
    """
    result = _graph.invoke({"raw_input": raw_input})
    return result["results"]
