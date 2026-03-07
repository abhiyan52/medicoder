"""
    author: @abhiyantimilsina
    description: State dict for medicoder
"""

from typing import Dict, List
from typing_extensions import TypedDict


class MedicoderState(TypedDict):
    raw_input: str                       # user-provided: file path or raw text
    clinical_note: str                   # resolved note content
    parsed_sections: Dict[str, List[str]]  # section name -> extracted text chunks
    conditions: List[dict]               # extracted conditions (condition + code)
    results: List[dict]                  # conditions + hcc_relevant flag