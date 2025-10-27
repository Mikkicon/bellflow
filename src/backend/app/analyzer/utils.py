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
# env_path = "/Users/mp/projects/bellflow/.env"
# print("env_path", env_path)
load_dotenv(dotenv_path=env_path)
vertexai.init(project="bellflow", location="us-central1")


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
            self.model = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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
        print("OPENAI_API_KEY:", OPENAI_API_KEY[:15])
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
            response: ParsedResponse = self.model.responses.parse(
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

# newsapi_tool_simple.py
# <100 lines. Minimal tool function you can register with your agent/LLM tool registry.
# Usage: register `newsapi_tool` as a callable tool. It accepts a dict-like payload and returns a dict.

import os, time, requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

BASE = "https://newsapi.org/v2/everything"
DEFAULT_PAGE_SIZE = 20
MAX_RETRIES = 3
BACKOFF = 1.0

def _normalize_article(a: Dict[str, Any]) -> Dict[str, Any]:
    src = a.get("source") or {}
    return {
        "source_id": src.get("id"),
        "source_name": src.get("name"),
        "author": a.get("author"),
        "title": a.get("title") or "",
        "description": a.get("description"),
        "url": a.get("url"),
        "urlToImage": a.get("urlToImage"),
        "publishedAt": a.get("publishedAt"),
        "content": a.get("content"),
    }

# @tool
def fetch_and_prepare_news(queries: List[str], n: int = 5, lang: str = "en") -> Dict[str, Any]:
    """ Fetch top new articles for `query` """
    api_key = os.getenv("NEWS_API_ORG_KEY")
    if not api_key:
        return {"status": "error", "message": "NEWSAPI_KEY required"}
    # Set default date range: 7 days ago to today
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    params = {
        "pageSize": max(DEFAULT_PAGE_SIZE, n), 
        "sortBy": "popularity", 
        "language": lang,
        "from": from_date,
        "to": to_date
    }
    raw = []
    for query in queries:
        resp = requests.get(BASE, params={**params, "q":query, "apiKey": api_key}, headers={"Accept": "application/json"}, timeout=8)
        data = resp.json()
        raw.extend(data.get("articles", [])[:n])
    print("raw")
    print(raw)
    articles = [_normalize_article(a) for a in raw]
    print("articles")
    print(articles)
    bullets: List[str] = []
    for a in articles:
        one_line = (a.get("description") or a.get("content") or "").split("\n")[0].strip()
        if not one_line:
            one_line = a["title"]
        date = a.get("publishedAt", "").split("T")[0]
        bullets.append(f"{a['title']} — {one_line} ({a.get('source_name')},{date}) — {a.get('url')}")
    combined = "\n".join(bullets)
    print("combined")
    print(combined)
    return {"status": "ok", "totalResults": data.get("totalResults", 0), "articles": articles, "combined_summary": combined}


