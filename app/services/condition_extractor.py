"""
author: @abhiyanhaze
description: Service / Tool to run the inference and get back the results.
"""

from app.utils.logger import logger
from app.config import settings
from app.utils.model_config_utils import ModelConfig, get_default_model_config
from langchain_google_vertexai import ChatVertexAI
from typing import Optional


class ConditionExtractor:
    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        # Use provided config or fallback to defaults
        self.config = config or get_default_model_config()
        
        logger.info("Initializing ConditionExtractor", 
                    model=self.config.model_name,
                    project=settings.PROJECT_ID)

        self.model = ChatVertexAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
        )
        