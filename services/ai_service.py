import os

from openai import OpenAI


class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_response(self, user_message: str) -> str:
        response = self.client.responses.create(model="gpt-5.4", input=user_message)
        return response.output_text
