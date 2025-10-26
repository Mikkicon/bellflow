from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Tuple
from openai import OpenAI
# from openai.resources.chat.completions.completions import ParsedResponse
from openai.types.shared_params.reasoning import Reasoning
from openai.types.responses import ParsedResponse
from vertexai.generative_models import GenerativeModel, GenerationConfig
import vertexai

from dotenv import load_dotenv
from pathlib import Path

# Load .env from the backend directory (2 levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
vertexai.init(project="bellflow", location="us-central1")


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"
# MODEL = "gpt-5-nano"
# MODEL = "gpt-o4‑mini"
REASONING = set(["o1-preview", "o1-mini", "gpt-5-pro", "gpt-5-mini", "gpt-5-nano", "o3-mini"])

class LLMClient:
    def __init__(self, provider: str = "openai", model_name: str = None):
        """
        Initialize the LLM client.
        :param provider: The provider to use ("openai" or "vertexai").
        :param model_name: The model name to use (e.g., "gpt-4o-mini" or "gemini-2.5-flash-lite").
        """
        self.provider = provider
        self.model_name = model_name or (
            MODEL if provider == "openai" else "gemini-2.5-flash-lite"
        )

        if provider == "vertexai":
            vertexai.init(project="bellflow", location="us-central1")
            self.model = GenerativeModel(self.model_name)
        elif provider == "openai":
            pass
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> ParsedResponse:
        """
        Generate a response using the selected LLM provider.
        :param messages: The chat history/messages for the model.
        :param kwargs: Additional parameters for the model.
        :return: The generated response text.
        """
        kwargs = kwargs or {}
        max_tokens = kwargs.pop("max_tokens", None)
        response_format = kwargs.pop("response_format", None)
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        print("OPENAI_API_KEY:", OPENAI_API_KEY[:5])
        if self.provider == "vertexai":
            prompt = "\n".join(
                [msg["content"] for msg in messages if msg["role"] == "user"]
            )
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_format,
                    max_output_tokens=max_tokens,
                    **kwargs,
                ),
            )
            return response.text
        elif self.provider == "openai":
            response: ParsedResponse = client.responses.parse(
                model=self.model_name,
                input=messages,
                reasoning=Reasoning(effort="medium", summary="concise") if (MODEL in REASONING) else None,
                text_format=response_format,
                **kwargs,
            )
            print("\n\nresponse\n")
            print(response)
            return response
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


def filter_posts(db_posts, limit=30):
    processed_posts = []
    for i, post in enumerate(db_posts):
        if i >= limit:
            break
        processed_posts.append(
            {
                "text": post.get("description"),
                "likes": post.get("likes", 0),
                "retweets": post.get("reposts", 0),
                "replies": post.get("replies", 0),
                "impressions": post.get("views", 0),
                "timestamp": post.get("date_posted"),
            }
        )

    return processed_posts
