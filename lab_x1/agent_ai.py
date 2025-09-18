import os

from dotenv import load_dotenv


from typing import Annotated

from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages




load_dotenv(override=True)

# Check the key
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print(
        "OpenAI API Key not set - please head to the troubleshooting guide in the setup folder"
    )



class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

import os
from langchain.chat_models import init_chat_model



llm = init_chat_model("openai:gpt-4.1")


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()