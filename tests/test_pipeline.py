from unittest.mock import patch

import pytest

from app.graph.medicoder_pipeline import _build_graph, run

def test_build_graph():
    # Verify graph compiles and contains expected nodes
    graph = _build_graph()
    assert graph is not None
    # Depending on langgraph API we can check nodes
    assert "input_handler" in graph.nodes
    assert "parser" in graph.nodes
    assert "extractor" in graph.nodes
    assert "evaluator" in graph.nodes

@patch("app.graph.medicoder_pipeline._graph.invoke")
def test_run_pipeline(mock_invoke):
    # Mock the return result of the graph
    mock_invoke.return_value = {
        "results": [
            {"condition": "Hypertension", "code": "I10", "hcc_relevant": True}
        ]
    }
    
    output = run("some raw input")
    
    mock_invoke.assert_called_once_with({"raw_input": "some raw input"})
    assert output == [{"condition": "Hypertension", "code": "I10", "hcc_relevant": True}]

@pytest.mark.integration
def test_integration_pipeline_real_llm():
    """
    Integration test that runs the entire pipeline end-to-end with real LLM inference.
    To run this test standalone:
    RUN_INTEGRATION_TESTS=1 poetry run pytest tests/test_pipeline.py::test_integration_pipeline_real_llm
    """
    simple_note = "Assessment / Plan: 1. Essential hypertension (I10). 2. Type 2 diabetes mellitus (E11.9)."
    
    # Run the pipeline without any mocks. This will hit the real models via LangGraph
    results = run(simple_note)
    
    # We expect some results
    assert isinstance(results, list)
    assert len(results) > 0, "Expected LLM to extract at least one condition"
    
    # Basic validation of expected output from LLM
    conditions_extracted = [str(res.get("condition", "")).lower() for res in results]
    
    # Verify the LLM picked up the key conditions from the text
    assert any("hypertension" in c for c in conditions_extracted), f"Expected to find hypertension in {conditions_extracted}"
    assert any("diabetes" in c for c in conditions_extracted), f"Expected to find diabetes in {conditions_extracted}"
    
    # Verify HCC mapping logic is working on the real outputs
    assert all("hcc_relevant" in res for res in results), "hcc_relevant flag is missing from results"
