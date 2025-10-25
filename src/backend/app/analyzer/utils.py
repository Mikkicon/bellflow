from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple
import openai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import vertexai

vertexai.init(project="bellflow", location="us-central1")




class LLMClient:
    def __init__(self, provider: str = "openai", model_name: str = None):
        """
        Initialize the LLM client.
        :param provider: The provider to use ("openai" or "vertexai").
        :param model_name: The model name to use (e.g., "gpt-4o-mini" or "gemini-2.5-flash-lite").
        """
        self.provider = provider
        self.model_name = model_name or (
            "gpt-4o-mini" if provider == "openai" else "gemini-2.5-flash-lite"
        )

        if provider == "vertexai":
            vertexai.init(project="bellflow", location="us-central1")
            self.model = GenerativeModel(self.model_name)
        elif provider == "openai":
            openai.api_key = "OPENAI_API_KEY"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response using the selected LLM provider.
        :param messages: The chat history/messages for the model.
        :param kwargs: Additional parameters for the model.
        :return: The generated response text.
        """
        kwargs = kwargs or {}
        max_tokens = kwargs.pop("max_tokens", None)
        response_schema = kwargs.pop("response_schema", None)
        
        if self.provider == "vertexai":
            prompt = "\n".join([msg["content"] for msg in messages if msg["role"] == "user"])
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    max_output_tokens=max_tokens,
                    **kwargs,
                ),
            )
            return response.text
        elif self.provider == "openai":
            response = openai.chat.completions.create(
                model=self.model_name, messages=messages, **kwargs
            )
            return response["choices"][0]["message"]["content"].strip()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")



def load_twitter_posts(file_path: str, limit=30) -> List[Dict[str, Any]]:
    """
    Load and process posts from a JSON file.
    :param file_path: Path to the JSON file containing posts.
    :return: List of processed posts.
    """
    with open(file_path, "r") as f:
        raw_posts = json.load(f)

    processed_posts = []
    for i, post in enumerate(raw_posts):
        if i >= limit:
            break
        processed_posts.append(
            {
                "post_id": post.get("id"),
                "text": post.get("description"),
                "likes": post.get("likes", 0),
                "retweets": post.get("reposts", 0),
                "replies": post.get("replies", 0),
                "impressions": post.get("views", 0),
                "timestamp": post.get("date_posted"),
                "media": (
                    "image"
                    if post.get("photos")
                    else "video" if post.get("videos") else "none"
                ),
            }
        )

    return processed_posts
