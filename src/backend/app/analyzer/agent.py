from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
from typing import Literal

from backend.app.analyzer.utils import LLMClient, load_twitter_posts


@dataclass
class AgentContext:
    posts: List[Dict[str, Any]]
    top_hashtags: Optional[List[str]] = None
    author_stats: Optional[Dict[str, Any]] = None


class SuggestedPost(BaseModel):
    text: str = Field(..., min_length=5, max_length=400)
    hashtags: List[str]
    media_suggestion: Literal["image", "video", "gif", "none"]
    predicted_engagement: Literal["low", "medium", "high"]
    rationale: str = Field(..., max_length=200)


class ResponseSchema(BaseModel):
    suggested_posts: List[SuggestedPost] = Field(..., min_length=3, max_length=3)


def build_prompt(
    context: AgentContext, chat_history: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Build the messages list for OpenAI ChatCompletion.
    Provide tools list and strict instructions for output format (CALL/FINAL_JSON).
    """
    system = (
        "You are a final-stage social media strategist agent. You MUST produce exactly one FINAL_JSON block "
        "containing three candidate posts in JSON conforming to the schema. "
        "Return a line starting with FINAL_JSON: followed by valid JSON.\n"
        "Do NOT output chain-of-thought. Output only the FINAL_JSON block (and short clarifying one-line comments are allowed)."
    )

    context_text = {
        "role": "system",
        "content": system
        + f"\n\nContext summary:\n- top_hashtags: {context.top_hashtags}\n- author_stats: {json.dumps(context.author_stats)}\n- posts_count: {len(context.posts)}\n",
    }
    messages = [context_text]
    # append conversation history (assistant/tool results and user)
    messages.extend(chat_history)
    # assistant kickoff: give the model an initial instruction to propose next actions
    kickoff = {
        "role": "user",
        "content": (
            "Create 3 candidate posts optimized for virality given the context. "
            "Use the available context to craft engaging posts that align with the author's style and audience."
        ),
    }
    messages.append(kickoff)
    return messages


def run_agent(
    context: AgentContext, max_steps: int = 1, provider: str = "vertexai"
) -> Dict[str, Any]:
    llm_client = LLMClient(provider=provider)
    chat_history: List[Dict[str, str]] = []
    steps = 0
    while steps < max_steps:
        messages = build_prompt(context, chat_history)
        # GENERATE
        assistant_text = llm_client.generate(
            messages,
            temperature=0.7,
            max_tokens=800,
            response_schema=ResponseSchema.model_json_schema(),
        )
        chat_history.append({"role": "assistant", "content": assistant_text})
        steps += 1
        return {"final": assistant_text, "chat_history": chat_history}


def main():
    """Full agent run with tools and multiple steps."""
    posts = load_twitter_posts(
        "/Users/mp/projects/bellflow/src/backend/tests/twitter-yanlecun-100-posts.json",
        limit=20,
    )
    # TODO author_stats = summarize_author_stats(recent_posts)
    # TODO top_hashtags = ["#AI", "#Productivity", "#Startup"]
    ctx = AgentContext(
        posts=posts,
        # author_stats=author_stats,
        # top_hashtags=top_hashtags,
    )
    print("Running Agent...")
    out = run_agent(ctx, provider="vertexai")
    print("--- FINAL CANDIDATES ---")
    print(json.dumps(out["final"], indent=2))


if __name__ == "__main__":
    main()
