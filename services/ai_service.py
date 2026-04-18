import logging

from openai import OpenAI

from core.config import settings
from core.prompts import BASE_SYSTEM_PROMPT, CODING_ASSISTANT_PROMPT, SUPPORT_ASSISTANT_PROMPT

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def get_prompt(self):
        if settings.assistant_mode == "coding":
            return CODING_ASSISTANT_PROMPT

        if settings.assistant_mode == "support":
            return SUPPORT_ASSISTANT_PROMPT

        return BASE_SYSTEM_PROMPT

    def generate_response(self, user_message: str) -> str:
        prompt = self.get_prompt()
        logger.info("Calling OpenAI API model=%s", settings.openai_model)
        try:
            response = self.client.responses.create(
                model=settings.openai_model, instructions=prompt, input=user_message
            )
            logger.info("OpenAI API response received")
            return response.output_text
        except Exception as e:
            logger.error("OpenAI API error: %s", str(e))
            raise
