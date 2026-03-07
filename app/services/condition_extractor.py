"""
author: @abhiyanhaze
description: Service / Tool to run the inference and get back the results.
"""

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import logger
from app.utils.model_config_utils import ModelConfig, get_default_model_config
from app.utils.prompt_loader import get_prompt


class ExtractionError(Exception):
    """Raised when condition extraction fails."""
    pass


# ------------------------------------
# Output Schema
# ------------------------------------


class ExtractedCondition(BaseModel):
    condition: str = Field(description="The name of the diagnosed medical condition")
    code: str = Field(description="The associated ICD-10-CM code")


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

        self.model = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            top_k=self.config.top_k,
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
        )

        self.parser = JsonOutputParser(pydantic_object=ExtractedCondition)

        # Eagerly load prompt and build chain once at init time
        prompt_text = get_prompt(self.PROMPT_NAME, self.PROMPT_VERSION)
        if not prompt_text:
            raise ExtractionError(f"Failed to load prompt: {self.PROMPT_NAME}")
        self._chain = self._build_chain(prompt_text)

    def _build_chain(self, prompt_text: str):
        """
        Build a LangChain LCEL chain: PromptTemplate | model | JsonOutputParser
        """
        prompt = PromptTemplate(
            template=prompt_text,
            input_variables=["clinical_text"],
        )
        return prompt | self.model | self.parser

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _invoke(self, note: str):
        return self._chain.invoke({"clinical_text": note})

    def extract(self, note: str) -> list[ExtractedCondition]:
        """
        Extract conditions from the given clinical note.
        Returns a list of ExtractedCondition objects.
        """
        logger.info("Running condition extraction", prompt_name=self.PROMPT_NAME)

        try:
            raw_result = self._invoke(note)
        except Exception as e:
            logger.error("chain.invoke failed during condition extraction",
                         prompt_name=self.PROMPT_NAME, error=str(e), exc_info=True)
            raise ExtractionError(f"Condition extraction chain failed: {e}") from e

        if not isinstance(raw_result, list):
            logger.error("chain.invoke returned unexpected type; expected list of dicts from JsonOutputParser",
                         actual_type=type(raw_result).__name__, raw_result=raw_result)
            raise ExtractionError(f"Unexpected output type from model: {type(raw_result).__name__}")

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
