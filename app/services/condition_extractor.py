"""
author: @abhiyanhaze
description: Service / Tool to run the inference and get back the results.
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from pydantic import BaseModel, Field

from app.config import settings
from app.utils.logger import logger
from app.utils.model_config_utils import ModelConfig, get_default_model_config
from app.utils.prompt_loader import get_prompt

# ------------------------------------
# Output Schema
# ------------------------------------


class ExtractedCondition(BaseModel):
    condition: str = Field(description="The name of the diagnosed medical condition")
    code: str = Field(description="The associated ICD-10-CM code")


class ExtractionResult(BaseModel):
    conditions: list[ExtractedCondition] = Field(default_factory=list)


# ------------------------------------
# Service
# ------------------------------------


class ConditionExtractor:
    PROMPT_NAME = "clinical_note_extraction"
    PROMPT_VERSION = None  # This will take the latest version by default

    def __init__(self, config: ModelConfig | None = None) -> None:
        self.config = config or get_default_model_config()

        logger.info(
            "Initializing ConditionExtractor",
            model=self.config.model_name,
            project=settings.PROJECT_ID,
        )

        self.model = ChatVertexAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
        )

        self.parser = JsonOutputParser(pydantic_object=ExtractedCondition)

    def _build_chain(self, prompt_text: str):
        """
        Build a LangChain LCEL chain: PromptTemplate | model | JsonOutputParser
        """
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["clinical_text"],
        )
        return prompt | self.model | self.parser

    def extract(self, note: str) -> list[ExtractedCondition]:
        """
        Extract conditions from the given clinical note.
        Returns a list of ExtractedCondition objects.
        """
        prompt_text = get_prompt(self.PROMPT_NAME, self.PROMPT_VERSION)
        if not prompt_text:
            logger.error("Failed to load prompt", prompt_name=self.PROMPT_NAME)
            return []

        logger.info("Running condition extraction", prompt_name=self.PROMPT_NAME)

        chain = self._build_chain(prompt_text)
        try:
            raw_result = chain.invoke({"clinical_text": note})
        except Exception as e:
            logger.error("chain.invoke failed during condition extraction",
                         prompt_name=self.PROMPT_NAME, error=str(e), exc_info=True)
            return []

        if not isinstance(raw_result, list):
            logger.error("chain.invoke returned unexpected type; expected list of dicts from JsonOutputParser",
                         actual_type=type(raw_result).__name__, raw_result=raw_result)
            return []

        # Build ExtractedCondition objects, skipping malformed or incomplete items
        conditions = []
        for item in raw_result:
            if not isinstance(item, dict):
                logger.warning("Skipping non-dict item in chain.invoke output",
                               actual_type=type(item).__name__, item=item)
                continue
            if not item.get("condition") or not item.get("code"):
                logger.warning("Skipping ExtractedCondition with missing fields", item=item)
                continue
            conditions.append(ExtractedCondition(**item))

        logger.info("Extraction complete", num_conditions=len(conditions))
        return conditions
