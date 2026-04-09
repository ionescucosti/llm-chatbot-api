import os

from openai import OpenAI

from core.config import settings
from core.prompts import BASE_SYSTEM_PROMPT, CODING_ASSISTANT_PROMPT, SUPPORT_ASSISTANT_PROMPT


class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def get_prompt(self):
        if settings.assistant_mode == "coding":
            return CODING_ASSISTANT_PROMPT

        if settings.assistant_mode == "support":
            return SUPPORT_ASSISTANT_PROMPT

        return BASE_SYSTEM_PROMPT

    def generate_response(self, user_message: str) -> str:
        prompt = self.get_prompt()
        response = self.client.responses.create(model=settings.openai_model, instructions=prompt, input=user_message)

        return response.output_text
