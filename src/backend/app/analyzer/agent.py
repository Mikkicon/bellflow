from __future__ import annotations
import os, json
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
from typing import Literal
import time
import logging
from bson import ObjectId
from datetime import datetime
from openai.types.responses import ParsedResponse
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain import hub
from langchain_community.llms import _import_openai
from langchain.agents import AgentExecutor, create_react_agent

from app.analyzer.utils import LLMClient, fetch_and_prepare_news
from app.database.connector import connect_database, get_collection
import asyncio

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


@dataclass
class AgentContext:
    posts: List[Dict[str, Any]]
    top_hashtags: Optional[List[str]] = None
    author_stats: Optional[Dict[str, Any]] = None


class Topic(BaseModel):
    topics: List[str]


class SuggestedPost(BaseModel):
    text: str = Field(..., min_length=5, max_length=400)
    hashtags: List[str]
    media_description: str = Field(..., max_length=10)
    estimated_likes: int = Field(...)
    estimated_comments: int = Field(...)
    estimated_reposts: int = Field(...)
    rationale: str = Field(..., max_length=200)


class ReasoningStep(BaseModel):
    text: str = Field(..., min_length=5, max_length=100)


class ResponseSchema(BaseModel):
    suggested_posts: List[SuggestedPost] = Field(..., min_length=3, max_length=3)
    reasoning_steps: List[ReasoningStep] = Field(..., min_length=5)


class AnalysisResult(BaseModel):
    raw: str = Field(...)
    final: str = Field(...)
    events: Any = Field(...)
    news: List[str] = Field(...)


def build_prompt() -> List[Dict[str, str]]:
    """
    Build the messages list for OpenAI ChatCompletion.
    Provide tools list and strict instructions for output format (CALL/FINAL_JSON).
    """

    context_text = {
        "role": "system",
        "content": (
            "You are a final-stage social media strategist agent. You MUST produce exactly one FINAL_JSON block "
            "containing three candidate posts in JSON conforming to the schema. "
            "Return a line starting with FINAL_JSON: followed by valid JSON.\n"
            "Do NOT output chain-of-thought. Output only the FINAL_JSON block (and short clarifying one-line comments are allowed)."
        ),
    }
    messages = [context_text]
    # append conversation history (assistant/tool results and user)
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


def run_agent(context: AgentContext, provider: str = "openai") -> AnalysisResult:
    # Simple 3-step pipeline:
    # 1) ask LLM for 3 topics based on recent posts
    # 2) fetch news for those topics
    # 3) ask LLM to generate 3 suggested posts using posts + news summary
    llm_client = LLMClient(provider=provider)

    # prepare a short text summary of recent posts
    posts_texts = [p.get("text", "") for p in (context.posts or [])][:10]
    posts_text = "\n".join([f"- {t}" for t in posts_texts if t])

    # Step 1: ask for 3 topics
    topic_prompt = [
        {
            "role": "system",
            "content": 'You are a concise assistant. Return a JSON array of three short topic phrases (e.g. ["topic1", "topic2", "topic3"]). No extra text.',
        },
        {
            "role": "user",
            "content": f"Given these recent posts:\n{posts_text}\nProvide exactly 3 concise topics (short phrases).",
        },
    ]
    resp_topics = llm_client.generate(
        topic_prompt, temperature=0.2, max_tokens=200, response_format=Topic
    )
    topics = resp_topics.output[0].content[0].parsed.topics
    print("\n\ntopics")
    print(topics)

    # Step 2: fetch news for topics (use helper)
    news_result = fetch_and_prepare_news(query=" OR ".join(topics), n=5)
    news_summary = (
        news_result.get("combined_summary") if isinstance(news_result, dict) else ""
    )
    print("\n\nnews_result")
    print(news_result)
    # Step 3: ask LLM to produce 3 suggested posts using posts + short news summary
    final_prompt = [
        {
            "role": "system",
            "content": "You are a social media strategist. Return exactly one FINAL_JSON block containing three candidate posts in JSON.",
        },
        {
            "role": "user",
            "content": f"Recent posts:\n{posts_text}\n\nLatest news summary:\n{news_summary}\n\nCreate 3 candidate posts optimized for virality, return JSON only.",
        },
    ]

    response = llm_client.generate(
        final_prompt,
        temperature=0.7,
        max_tokens=800,
        response_format=ResponseSchema,
    )
    print("\n\nfinal")
    print(response)

    raw = response.model_dump_json()
    final_text = response.output[0].content[0].text
    events = [
        s.model_dump() for s in response.output[0].content[0].parsed.reasoning_steps
    ]
    return AnalysisResult(
        raw=raw, final=final_text, events=events, news=[ar["title"] for ar in news_result["articles"]]
    )


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


class AnalysisPoller:
    """
    Polls the database for completed scraper entries and runs analysis on them.
    """

    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self.logger = logging.getLogger(__name__)

    def poll_and_analyze(self):
        try:
            collection = get_collection("raw_data")
            if collection is None:
                self.logger.error("Failed to connect to database")
                return
            entries = collection.find({"status": "retriever:completed"}, limit=10)
            for entry in entries:
                try:
                    self._process_entry(entry, collection)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process entry {entry.get('id', 'unknown')}: {e}"
                    )
        except Exception as e:
            self.logger.error(f"Error during polling: {e}")

    def _process_entry(self, entry: Dict[str, Any], collection):
        try:
            # Parse raw_data JSON
            raw_data_str = entry.get("raw_data", "")
            if not raw_data_str:
                self.logger.warning(f"Empty raw_data for entry {entry.get('id')}")
                self._update_entry_with_error(entry, "Empty raw_data", collection)
                return
            raw_data = json.loads(raw_data_str)
            posts_data = raw_data.get("items", [])
            if not posts_data:
                self.logger.warning(f"No posts found in entry {entry.get('id')}")
                self._update_entry_with_error(
                    entry, "No posts found in raw_data", collection
                )
                return

            # Filter and sort posts
            filtered_posts = self._filter_and_sort_posts(posts_data)
            if not filtered_posts:
                self.logger.warning(
                    f"No valid posts after filtering for entry {entry.get('id')}"
                )
                self._update_entry_with_error(
                    entry, "No valid posts after filtering", collection
                )
                return

            # Run agent analysis
            result = self._run_analysis(filtered_posts)
            self._update_entry_with_analysis(entry, result, collection)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse raw_data JSON: {str(e)}"
            self.logger.error(
                f"Failed to parse raw_data JSON for entry {entry.get('id')}: {e}"
            )
            self._update_entry_with_error(entry, error_msg, collection)
        except Exception as e:
            error_msg = f"Error processing entry: {str(e)}"
            self.logger.error(f"Error processing entry {entry.get('id')}: {e}")
            self._update_entry_with_error(entry, error_msg, collection)

    def _filter_and_sort_posts(
        self, posts_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        filtered_posts = []
        for post in posts_data:
            filtered_post = {
                "text": post.get("text", ""),
                "likes": post.get("likes", 0) or 0,
                "retweets": post.get("reposts", 0) or 0,
                "replies": post.get("comments", 0) or 0,
                "impressions": post.get("views", 0) or 0,
                "timestamp": post.get("date_posted", ""),
            }
            if filtered_post["text"]:
                filtered_posts.append(filtered_post)
        # Sort by likes (descending)
        filtered_posts.sort(key=lambda x: x["likes"], reverse=True)
        return filtered_posts

    def _run_analysis(self, posts: List[Dict[str, Any]]):
        try:
            # Create agent context
            context = AgentContext(posts=posts)
            # Run agent
            result = run_agent(context)
            # Return the final analysis as JSON string
            return result
        except Exception as e:
            self.logger.error(f"Error running agent analysis: {e}")
            # Re-raise the exception so it can be handled by _process_entry
            raise Exception(f"Analysis failed: {str(e)}")

    def _update_entry_with_analysis(self, entry: Dict[str, Any], analysis: AnalysisResult, collection):
        try:
            # Update the entry
            result = collection.update_one(
                {"_id": entry["_id"]},
                {
                    "$set": {
                        "raw_analysis": analysis.raw,
                        "analysis": analysis.final,
                        "news": analysis.news,
                        "events": analysis.events,
                        "status": "analyzer:completed",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            if result.modified_count > 0:
                self.logger.info(f"Successfully updated entry {entry.get('id')} with analysis")
            else:
                self.logger.warning(f"No document updated for entry {entry.get('id')}")
        except Exception as e:
            self.logger.error(f"Failed to update entry {entry.get('id')} with analysis: {e}")

    def _update_entry_with_error(
        self, entry: Dict[str, Any], error_message: str, collection
    ):
        """
        Update the entry with error information and set status to analyzer:failed.
        """
        try:
            result = collection.update_one(
                {"_id": entry["_id"]},
                {
                    "$set": {
                        "error": error_message,
                        "status": "analyzer:failed",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            if result.modified_count > 0:
                self.logger.info(
                    f"Successfully updated entry {entry.get('id')} with error status"
                )
            else:
                self.logger.warning(
                    f"No document updated for entry {entry.get('id')} with error"
                )
        except Exception as e:
            self.logger.error(
                f"Failed to update entry {entry.get('id')} with error: {e}"
            )

    def start_polling(self):
        """
        Start continuous polling loop.
        """
        self.logger.info(
            f"Starting analysis poller with {self.poll_interval}s interval"
        )

        while True:
            try:
                self.poll_and_analyze()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.logger.info("Polling stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in polling loop: {e}")
                time.sleep(self.poll_interval)

    def run_once(self):
        self.logger.info("Running analysis polling once")
        self.poll_and_analyze()


async def startup_event():
    """Initialize database connection on startup."""
    try:
        if connect_database():
            print("Database connected successfully")
        else:
            print("Failed to connect to database")
    except Exception as e:
        print(f"Database connection error: {e}")


async def main():
    # Example usage:
    # main()  # Run original agent example
    await startup_event()
    # To run the poller:
    poller = AnalysisPoller()
    # poller.run_once()  # Run once for testing
    poller.start_polling()  # Or start continuous polling


if __name__ == "__main__":
    asyncio.run(main())
