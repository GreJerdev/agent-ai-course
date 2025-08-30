from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from openai import OpenAI
import json

load_dotenv(override=True)

# Check the key - if you're not using OpenAI, check whichever key you're using! Ollama doesn't need a key.
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print(
        "OpenAI API Key not set - please head to the troubleshooting guide in the setup folder"
    )


def init_openai():
    openai = OpenAI(api_key=openai_api_key)
    return openai


# Define the state structure
class HaikuState(TypedDict):
    haiku: str
    rating: int
    reason: str
    messages: list


def write_haiku(state: HaikuState) -> HaikuState:
    """First node: Write a haiku about the sea"""
    client = init_openai()
    
    rules = [
        {
            "role": "system",
            "content": "You are a helpful assistant that writes blog posts.",
        },
        {"role": "user", "content": "Write me a haiku about the sea."},
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=rules,
        temperature=0.7,
        max_tokens=100,
    )
    
    haiku = response.choices[0].message.content
    
    # Update state
    state["haiku"] = haiku
    state["messages"] = rules + [{"role": "assistant", "content": haiku}]
    
    print(f"Generated haiku: {haiku}")
    return state


def rate_haiku(state: HaikuState) -> HaikuState:
    """Second node: Rate the haiku and provide reason"""
    client = init_openai()
    
    rules_second_part = [
        {"role": "system", "content": "You are an expert in haiku about the sea."},
        {"role": "user", "content": f"Rate the level of this haiku from 1 to 10 and provide a reason. Return your response as a JSON with exactly two keys: 'rate' (integer 1-10) and 'reason' (string explaining the rating). Haiku: {state['haiku']}"},
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=rules_second_part,
        temperature=0.7,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    
    try:
        rating_data = json.loads(response.choices[0].message.content)
        state["rating"] = rating_data.get("rate", 5)
        state["reason"] = rating_data.get("reason", "No reason provided")
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        state["rating"] = 5
        state["reason"] = "Error parsing rating response"
    
    print(f"Rating: {state['rating']}/10")
    print(f"Reason: {state['reason']}")
    
    return state


def create_haiku_workflow():
    """Create the LangGraph workflow"""
    
    # Create the graph
    workflow = StateGraph(HaikuState)
    
    # Add nodes
    workflow.add_node("write_haiku", write_haiku)
    workflow.add_node("rate_haiku", rate_haiku)
    
    # Set entry point
    workflow.set_entry_point("write_haiku")
    
    # Define the flow
    workflow.add_edge("write_haiku", "rate_haiku")
    workflow.add_edge("rate_haiku", END)
    
    # Compile the graph
    return workflow.compile()


def main():
    """Main function to run the haiku workflow"""
    
    # Initialize the workflow
    app = create_haiku_workflow()
    
    # Print the app graph structure
    print("="*50)
    print("APP GRAPH STRUCTURE:")
    print("="*50)
    print(app.get_graph().draw_mermaid())
    print("="*50)
    
    # Initialize the state
    initial_state = {
        "haiku": "",
        "rating": 0,
        "reason": "",
        "messages": []
    }
    
    # Run the workflow
    print("Starting haiku generation and rating workflow...")
    result = app.invoke(initial_state)
    
    # Print final results
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print("="*50)
    print(f"Haiku: {result['haiku']}")
    print(f"Rating: {result['rating']}/10")
    print(f"Reason: {result['reason']}")
    print("="*50)
    print(result)
    print("="*50)
    return result


if __name__ == "__main__":
    main()
