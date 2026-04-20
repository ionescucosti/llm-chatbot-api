import logging

from openai import OpenAI

from core.config import settings
from core.prompts import RAG_SYSTEM_PROMPT
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_service = EmbeddingService()

    def generate_response(self, chat_history: list[dict], top_k: int = 5) -> str:
        """Generate a response using RAG (Retrieval Augmented Generation)."""
        # Get the latest user message for retrieval
        user_message = ""
        for msg in reversed(chat_history):
            if msg["role"] == "user":
                user_message = msg["content"]
                break

        if not user_message:
            return "No user message found in the conversation."

        # Generate embedding for the query
        logger.info("Generating embedding for RAG query")
        query_embedding = self.embedding_service.generate_single_embedding(user_message)

        # Search for relevant documents
        logger.info("Searching for relevant documents")
        search_results = self.embedding_service.search_chroma(query_embedding, top_k=top_k)

        if not search_results:
            logger.info("No relevant documents found, falling back to plain response")
            context = "No relevant documents found in the knowledge base."
        else:
            # Build context from search results
            context_parts = []
            for i, result in enumerate(search_results, 1):
                source = result.get("document_filename", "Unknown")
                content = result.get("content", "")
                score = result.get("score", 0)
                context_parts.append(f"[{i}] Source: {source} (relevance: {score:.2f})\n{content}")
            context = "\n\n".join(context_parts)

        # Build the prompt with context
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)

        logger.info("Calling OpenAI API for RAG response model=%s", settings.openai_model)
        try:
            response = self.client.responses.create(
                model=settings.openai_model,
                instructions=system_prompt,
                input=chat_history,
            )
            logger.info("OpenAI API RAG response received")
            return response.output_text
        except Exception as e:
            logger.error("OpenAI API error in RAG: %s", str(e))
            raise
