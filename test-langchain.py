import os
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain.output_parsers import StructuredOutputParser, ResponseSchema as LCResponseSchema
from langchain import hub
from langchain_community.llms import _import_openai
from langchain.agents import AgentExecutor, create_react_agent

from dotenv import load_dotenv

from src.backend.app.analyzer.agent import ResponseSchema, build_prompt
from src.backend.app.analyzer.utils import fetch_and_prepare_news
import json

load_dotenv(dotenv_path=".env")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", "You are a helpful assistant"),
#         ("placeholder", "{chat_history}"),
#         ("human", "{input}"),
#         ("placeholder", "{agent_scratchpad}"),
#     ]
# # )
# model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


# @tool
# def magic_function(input: int) -> int:
#     """Applies a magic function to an input."""
#     return input + 2


# tools = [magic_function]

# agent = create_tool_calling_agent(model, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# agent_executor.invoke({"input": "what is the value of magic_function(3)?"})

# agent_executor.invoke(
#     {
#         "input": "what's my name?",
#         "chat_history": [
#             HumanMessage(content="hi! my name is bob"),
#             AIMessage(content="Hello Bob! How can I assist you today?"),
#         ],
#     }
# )


# GENERATE
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a final-stage social media strategist agent. You MUST produce exactly one FINAL_JSON block "
                "containing three candidate posts in JSON conforming to the schema. "
                "Return a line starting with FINAL_JSON: followed by valid JSON.\n"
                "Do NOT output chain-of-thought. Output only the FINAL_JSON block (and short clarifying one-line comments are allowed)."
            ),
        ),
        ("placeholder", "{chat_history}"),
        (
            "human",
            (
                "Create 3 candidate posts optimized for virality given the context. "
                "Use the available context to craft engaging posts that align with the author's style and audience."
            ),
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

# Build a StructuredOutputParser and extract format instructions that the
# model should follow. This avoids wrapping the LLM (which can remove
# low-level methods like bind_tools) while still providing a strict
# response format the agent must produce.
response_schemas = [
    LCResponseSchema(
        name="suggested_posts",
        description=(
            "A JSON array of exactly 3 post objects. Each object must have:"
            " text (string), hashtags (array of strings), media_description (string),"
            " estimated_likes (int), estimated_comments (int), estimated_reposts (int),"
            " rationale (string)."
        ),
    ),
    LCResponseSchema(
        name="reasoning_steps",
        description=(
            "A list of short reasoning step strings explaining why the posts were chosen."
            " Provide at least 5 items."
        ),
    ),
]

parser = StructuredOutputParser.from_response_schemas(response_schemas)
RESPONSE_FORMAT = parser.get_format_instructions()
# Escape curly braces in the format instructions so ChatPromptTemplate doesn't
# treat JSON braces as template variables. ChatPromptTemplate uses `{}` for
# placeholders, so we double them to escape.
RESPONSE_FORMAT_ESCAPED = RESPONSE_FORMAT.replace("{", "{{").replace("}", "}}")

# Inject the format instructions into the system prompt so the model knows
# to return a FINAL_JSON line followed by JSON that matches the schema.
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a final-stage social media strategist agent. You MUST produce exactly one FINAL_JSON block "
                "containing three candidate posts in JSON conforming to the schema. "
                "Return a line starting with FINAL_JSON: followed by valid JSON.\n"
                "Do NOT output chain-of-thought. Output only the FINAL_JSON block (and short clarifying one-line comments are allowed).\n\n"
                + RESPONSE_FORMAT_ESCAPED
            ),
        ),
        ("placeholder", "{chat_history}"),
        (
            "human",
            (
                "Create 3 candidate posts optimized for virality given the context. "
                "Use the available context to craft engaging posts that align with the author's style and audience."
            ),
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

tools = [fetch_and_prepare_news]
agent = create_tool_calling_agent(
    model,
    tools,
    prompt,
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
# Load the first 3 posts from the JSON file
with open("/Users/mp/projects/bellflow/src/backend/data/twitter-yanlecun-100-posts.json", "r") as f:
    posts_data = json.load(f)

# Extract descriptions from first 3 posts
descriptions = [post["description"] for post in posts_data[:3]]
input_text = " ".join(descriptions)

response = agent_executor.invoke({"input": input_text})
print(response)
# AnalysisResult(raw=response.model_dump_json(), final=response.output[0].content[0].text, events=[s.model_dump() for s in response.output[0].content[0].parsed.reasoning_steps])
