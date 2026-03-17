"""
    author: @abhiyantimilsina
    description: Nodes for langgraph
"""

from pathlib import Path
from typing import Dict

from app.services.clinical_note_parser import build_default_clinical_parser
from app.services.condition_extractor import ConditionExtractor
from app.services.hcc_evaluator import HCCRelevanceEvaluator
from app.graph.states import MedicoderState
from app.utils.logger import logger

HCC_CSV_PATH = Path(__file__).parent.parent.parent / "data" / "HCC_relevant_codes.csv"

_condition_extractor: ConditionExtractor | None = None
_hcc_evaluator: HCCRelevanceEvaluator | None = None


def _get_condition_extractor() -> ConditionExtractor:
    global _condition_extractor
    if _condition_extractor is None:
        _condition_extractor = ConditionExtractor()
    return _condition_extractor


def _get_hcc_evaluator() -> HCCRelevanceEvaluator:
    global _hcc_evaluator
    if _hcc_evaluator is None:
        _hcc_evaluator = HCCRelevanceEvaluator(HCC_CSV_PATH)
    return _hcc_evaluator


def input_handler_node(state: MedicoderState) -> Dict:
    """
    Passes extracted document text through to the pipeline.
    """
    clinical_note = state["raw_input"]
    if not clinical_note:
        raise ValueError("No text content provided")
    logger.info("Input received from uploaded document")
    return {"clinical_note": clinical_note}


def clinical_note_parser_node(state: MedicoderState) -> Dict:
    parser = build_default_clinical_parser()
    parsed_sections = parser.parse(state["clinical_note"])
    logger.info("Parsed clinical note", sections=list(parsed_sections.keys()))
    return {"parsed_sections": parsed_sections}


def condition_extractor_node(state: MedicoderState) -> Dict:
    extractor = _get_condition_extractor()

    # Prefer the parsed assessment_plan section; fall back to the full note
    sections = state["parsed_sections"]
    assessment_text = " ".join(sections.get("assessment_plan", []))
    
    if assessment_text:
        logger.info("Using parsed assessment_plan section for extraction")
        note_text = assessment_text
    else:
        logger.warning("No assessment_plan section detected; falling back to full clinical note for inference")
        note_text = state["clinical_note"]

    conditions = extractor.extract(note_text)
    return {"conditions": [c.model_dump() for c in conditions]}


def hcc_relevance_checker_node(state: MedicoderState) -> Dict:
    evaluator = _get_hcc_evaluator()
    results = evaluator.evaluate(state["conditions"])
    return {"results": results}
