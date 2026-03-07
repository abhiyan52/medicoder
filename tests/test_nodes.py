import pytest
from unittest.mock import patch, MagicMock
from app.graph.nodes import (
    input_handler_node,
    clinical_note_parser_node,
    condition_extractor_node,
    hcc_relevance_checker_node,
    _get_condition_extractor,
    _get_hcc_evaluator
)
from app.services.condition_extractor import ExtractedCondition
from app.graph.states import MedicoderState

@pytest.fixture
def dummy_state() -> MedicoderState:
    return {
        "raw_input": "",
        "clinical_note": "",
        "parsed_sections": {},
        "conditions": [],
        "results": [],
    }

def test_input_handler_node_raw_text(dummy_state):
    dummy_state["raw_input"] = "This is a raw clinical note."
    result = input_handler_node(dummy_state)
    assert result == {"clinical_note": "This is a raw clinical note."}

@patch("app.graph.nodes.load_file_from_path")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_file")
def test_input_handler_node_file_path(mock_is_file, mock_exists, mock_load, dummy_state):
    mock_exists.return_value = True
    mock_is_file.return_value = True
    mock_load.return_value = "Content from file"
    
    dummy_state["raw_input"] = "dummy/path.txt"
    result = input_handler_node(dummy_state)
    assert result == {"clinical_note": "Content from file"}

@patch("app.graph.nodes.load_file_from_path")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_file")
def test_input_handler_node_missing_file_content(mock_is_file, mock_exists, mock_load, dummy_state):
    mock_exists.return_value = True
    mock_is_file.return_value = True
    mock_load.return_value = None
    
    dummy_state["raw_input"] = "dummy/path.txt"
    with pytest.raises(ValueError, match="Failed to load clinical note from file"):
        input_handler_node(dummy_state)

@patch("app.graph.nodes.build_default_clinical_parser")
def test_clinical_note_parser_node(mock_build, dummy_state):
    mock_parser = MagicMock()
    mock_parser.parse.return_value = {"assessment_plan": ["plan 1", "plan 2"]}
    mock_build.return_value = mock_parser
    
    dummy_state["clinical_note"] = "Note content"
    result = clinical_note_parser_node(dummy_state)
    assert result == {"parsed_sections": {"assessment_plan": ["plan 1", "plan 2"]}}
    mock_parser.parse.assert_called_once_with("Note content")

@patch("app.graph.nodes._get_condition_extractor")
def test_condition_extractor_node_with_parsed_section(mock_get_extractor, dummy_state):
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = [
        ExtractedCondition(condition="Diabetes", code="E11.9")
    ]
    mock_get_extractor.return_value = mock_extractor
    
    dummy_state["clinical_note"] = "Full note content"
    dummy_state["parsed_sections"] = {"assessment_plan": ["patient has Diabetes"]}
    
    result = condition_extractor_node(dummy_state)
    assert result == {"conditions": [{"condition": "Diabetes", "code": "E11.9"}]}
    mock_extractor.extract.assert_called_once_with("patient has Diabetes")

@patch("app.graph.nodes._get_condition_extractor")
def test_condition_extractor_node_fallback_full_note(mock_get_extractor, dummy_state):
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = []
    mock_get_extractor.return_value = mock_extractor
    
    dummy_state["clinical_note"] = "Full note content"
    dummy_state["parsed_sections"] = {}  # Empty so it falls back
    
    result = condition_extractor_node(dummy_state)
    assert result == {"conditions": []}
    mock_extractor.extract.assert_called_once_with("Full note content")

@patch("app.graph.nodes._get_hcc_evaluator")
def test_hcc_relevance_checker_node(mock_get_evaluator, dummy_state):
    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.return_value = [
        {"condition": "Diabetes", "code": "E11.9", "hcc_relevant": True}
    ]
    mock_get_evaluator.return_value = mock_evaluator
    
    dummy_state["conditions"] = [{"condition": "Diabetes", "code": "E11.9"}]
    
    result = hcc_relevance_checker_node(dummy_state)
    assert result == {"results": [{"condition": "Diabetes", "code": "E11.9", "hcc_relevant": True}]}
    mock_evaluator.evaluate.assert_called_once_with([{"condition": "Diabetes", "code": "E11.9"}])

@patch("app.graph.nodes.ConditionExtractor")
def test_get_condition_extractor(mock_extractor_class):
    # Ensure global is reset for test isolation
    import app.graph.nodes as nodes_module
    nodes_module._condition_extractor = None
    
    mock_instance = MagicMock()
    mock_extractor_class.return_value = mock_instance
    
    ext1 = _get_condition_extractor()
    ext2 = _get_condition_extractor()
    
    assert ext1 is mock_instance
    assert ext2 is mock_instance
    mock_extractor_class.assert_called_once()
    
@patch("app.graph.nodes.HCCRelevanceEvaluator")
def test_get_hcc_evaluator(mock_evaluator_class):
    # Ensure global is reset for test isolation
    import app.graph.nodes as nodes_module
    nodes_module._hcc_evaluator = None
    
    mock_instance = MagicMock()
    mock_evaluator_class.return_value = mock_instance
    
    ev1 = _get_hcc_evaluator()
    ev2 = _get_hcc_evaluator()
    
    assert ev1 is mock_instance
    assert ev2 is mock_instance
    mock_evaluator_class.assert_called_once()
