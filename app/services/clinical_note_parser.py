"""
author: @abhiyanhaze
description: Parse classes for parsing the clinical notes file.
Currently only Regexbased parser is implemented.
"""

import re
from abc import ABC, abstractmethod

from app.utils.logger import logger


class ClinicalNoteParser(ABC):
    @abstractmethod
    def parse(self, note: str) -> dict[str, list[str]]:
        pass


class RegexBasedParser(ClinicalNoteParser):
    def __init__(self, *args, **kwargs):
        logger.info("Initializing RegexBasedParser")
        self._registry = {}
        super().__init__(*args, **kwargs)

    # ------------------------------
    # Pattern Registration
    # ------------------------------
    def register(self, section: str, pattern: str) -> None:
        """
        Register a regex pattern for a specific section.
        """
        if section not in self._registry:
            logger.info("Registering pattern for section", section=section)
            self._registry[section] = []

        self._registry[section].append(pattern)

    def get_patterns(self, section: str) -> list[str]:
        """
        Retrieve patterns registered for a section.
        """
        return self._registry.get(section, [])

    def parse(self, note: str) -> dict[str, list[str]]:
        """
        Parse the content of notes
        """
        results = {}

        for section, patterns in self._registry.items():
            section_results = []
            logger.info(
                "Evaluating patterns for section",
                section=section,
                num_patterns=len(patterns),
            )

            for pattern in patterns:
                # finditer will find all non-overlapping matches in the document
                for match in re.finditer(pattern, note, re.DOTALL | re.IGNORECASE):
                    if match.groups():
                        section_results.append(match.group(1).strip())
                if section_results:
                    # First successful pattern wins; skip remaining fallbacks
                    break

            if section_results:
                results[section] = section_results
            else:
                logger.info("No pattern found for section", section=section)

        return results


def build_default_clinical_parser() -> RegexBasedParser:
    """
    Creates a RegexBasedParser preloaded with common
    clinical note section patterns.
    """

    parser = RegexBasedParser()

    # Assessment / Plan patterns
    parser.register(
        "assessment_plan",
        r"Assessment\s*/\s*Plan\s*(.*?)(?:Return to Office|Encounter Sign-Off|$)",
    )

    parser.register(
        "assessment_plan",
        r"Assessment\s+and\s+Plan\s*(.*?)(?:Return to Office|Encounter Sign-Off|$)",
    )

    parser.register(
        "assessment_plan",
        r"Assessment\s*[:\-]?\s*(.*?)(?:Return to Office|Encounter Sign-Off|$)",
    )

    return parser
