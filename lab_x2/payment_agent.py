#!/usr/bin/env python3
"""
OpenAI + LangGraph agent for querying payment methods from a pandas DataFrame.

This agent:
1. Parses user input to extract country and payment type
2. Normalizes country names to ISO alpha-2 codes
3. Queries a pandas DataFrame for matching payment methods
4. Returns results in a structured JSON format
"""

import os
import json
import re
import pandas as pd
import pycountry
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


# Environment setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class PaymentQuery:
    """Structured representation of a payment query."""
    country_text: str
    payment_type: Optional[str] = None


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    user_input: str
    parsed_query: Optional[PaymentQuery]
    result: Optional[Dict[str, Any]]


def normalize_country_to_alpha2(text: str) -> Optional[str]:
    """
    Normalize various country name formats to ISO 3166-1 alpha-2 code.
    
    Args:
        text: Country name in various formats (e.g., "US", "United States", "usa")
        
    Returns:
        ISO alpha-2 code (e.g., "US") or None if invalid/ambiguous
    """
    if not text or not isinstance(text, str):
        return None
    
    # Clean the input
    text = text.strip().upper()
    
    # Handle common special cases
    country_mappings = {
        "UK": "GB",
        "UNITED KINGDOM": "GB", 
        "GREAT BRITAIN": "GB",
        "BRITAIN": "GB",
        "USA": "US",
        "UNITED STATES": "US",
        "UNITED STATES OF AMERICA": "US",
        "AMERICA": "US",
    }
    
    if text in country_mappings:
        return country_mappings[text]
    
    # If already 2-letter code, validate it
    if len(text) == 2:
        try:
            country = pycountry.countries.get(alpha_2=text)
            return country.alpha_2 if country else None
        except:
            return None
    
    # Try to find by name
    try:
        # First try exact match
        country = pycountry.countries.get(name=text.title())
        if country:
            return country.alpha_2
            
        # Try partial match
        matches = []
        for country in pycountry.countries:
            if text in country.name.upper():
                matches.append(country)
        
        # If exactly one match, return it
        if len(matches) == 1:
            return matches[0].alpha_2
            
    except:
        pass
    
    return None


def parse_user_input(message: str) -> PaymentQuery:
    """
    Parse user message to extract country and optional payment type.
    
    Args:
        message: User input message
        
    Returns:
        PaymentQuery with extracted information
    """
    if not message:
        return PaymentQuery("")
    
    # Clean the message
    message = message.strip().lower()
    
    # Extract payment type with synonyms
    payment_type = None
    payment_patterns = {
        "card": [r"\bcard\b", r"\bcredit\b", r"\bdebit\b"],
        "bank": [r"\bbank\b", r"\btransfer\b", r"\bbank transfer\b"],
    }
    
    for ptype, patterns in payment_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message):
                payment_type = ptype
                break
        if payment_type:
            break
    
    # Remove payment type words to isolate country
    words_to_remove = ["card", "credit", "debit", "bank", "transfer", "methods", "for", "list", "please", "show", "get"]
    country_text = message
    for word in words_to_remove:
        country_text = re.sub(rf"\b{word}\b", "", country_text)
    
    # Clean up extra spaces and punctuation
    country_text = re.sub(r'[^\w\s]', '', country_text).strip()
    country_text = ' '.join(country_text.split())  # Normalize whitespace
    
    return PaymentQuery(country_text=country_text, payment_type=payment_type)


def query_df(country_alpha2: str, payment_type: Optional[str], df: pd.DataFrame) -> List[str]:
    """
    Query the DataFrame for matching payment methods.
    
    Args:
        country_alpha2: ISO alpha-2 country code
        payment_type: Optional payment type ("card" or "bank")
        df: DataFrame with columns: country, payment_method_type, payment_method_type_name
        
    Returns:
        Sorted list of unique payment method type names
    """
    if df.empty:
        return []
    
    # Filter by country
    filtered_df = df[df['country'] == country_alpha2]
    
    # Filter by payment type if provided
    if payment_type:
        filtered_df = filtered_df[filtered_df['payment_method_type'] == payment_type]
    
    # Get unique payment method names and sort
    if filtered_df.empty:
        return []
    
    unique_types = filtered_df['payment_method_type_name'].unique()
    return sorted(unique_types.tolist())


def llm_node(state: AgentState) -> Dict[str, Any]:
    """LLM node that parses user input into structured fields."""
    user_input = state["user_input"]
    
    system_prompt = """You are a payment method query parser. Parse the user's message to extract:
1. Country name (required) - can be in any format
2. Payment type (optional) - can be any of the following: "card", "bank", "wallet", "ewallet", "on-screen QR", "card_redirect", "card_to_card", "cash_redirect", "pos"

The user might say things like:
- "US card" (country: US, payment_type: card)
- "United Kingdom" (country: United Kingdom, payment_type: null)
- "Please list bank methods for br" (country: br, payment_type: bank)

Respond ONLY with a JSON object in this exact format:
{"country_text": "extracted country text", "payment_type": "card|bank|null"}

If no clear country is found, use an empty string for country_text.
Payment type synonyms: credit/debit → card, transfer/bank transfer → bank
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        parsed_json = json.loads(response.choices[0].message.content)
        country_text = parsed_json.get("country_text", "")
        payment_type = parsed_json.get("payment_type")
        if payment_type == "null":
            payment_type = None
            
        parsed_query = PaymentQuery(country_text=country_text, payment_type=payment_type)
        
    except Exception as e:
        # Fallback to simple parsing
        parsed_query = parse_user_input(user_input)
    
    return {"parsed_query": parsed_query}


def tool_node(state: AgentState) -> Dict[str, Any]:
    """Tool node that queries the pandas DataFrame."""
    parsed_query = state["parsed_query"]
    
    if not parsed_query or not parsed_query.country_text:
        return {
            "result": {
                "country": None,
                "payment_type": parsed_query.payment_type if parsed_query else None,
                "count": 0,
                "types": [],
                "note": "No country specified in input"
            }
        }
    
    # Normalize country
    country_alpha2 = normalize_country_to_alpha2(parsed_query.country_text)
    
    if not country_alpha2:
        return {
            "result": {
                "country": None,
                "payment_type": parsed_query.payment_type,
                "count": 0,
                "types": [],
                "note": "Invalid country"
            }
        }
    
    # Get DataFrame (in real usage this would be passed to the function)
    df = get_demo_dataframe()
    
    # Query DataFrame
    payment_types = query_df(country_alpha2, parsed_query.payment_type, df)
    
    note = ""
    if not payment_types:
        if parsed_query.payment_type:
            note = f"No {parsed_query.payment_type} payment methods found for {country_alpha2}"
        else:
            note = f"No payment methods found for {country_alpha2}"
    
    return {
        "result": {
            "country": country_alpha2,
            "payment_type": parsed_query.payment_type,
            "count": len(payment_types),
            "types": payment_types,
            "note": note
        }
    }


def build_graph() -> StateGraph:
    """Build and return the LangGraph StateGraph."""
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("llm", llm_node)
    workflow.add_node("tool", tool_node)
    
    # Add edges
    workflow.set_entry_point("llm")
    workflow.add_edge("llm", "tool")
    workflow.add_edge("tool", END)
    
    return workflow.compile()


def get_demo_dataframe() -> pd.DataFrame:




    """Create a demo DataFrame for testing."""
    df_payment_methods_types = pd.read_csv("data/payment_methods_types.csv")
    return df_payment_methods_types
    data = [
        # US payment methods
        {"country": "US", "payment_method_type": "card", "payment_method_type_name": "visa"},
        {"country": "US", "payment_method_type": "card", "payment_method_type_name": "mastercard"},
        {"country": "US", "payment_method_type": "card", "payment_method_type_name": "amex"},
        {"country": "US", "payment_method_type": "bank", "payment_method_type_name": "ach"},
        {"country": "US", "payment_method_type": "bank", "payment_method_type_name": "wire_transfer"},
        
        # GB payment methods
        {"country": "GB", "payment_method_type": "card", "payment_method_type_name": "visa"},
        {"country": "GB", "payment_method_type": "card", "payment_method_type_name": "mastercard"},
        {"country": "GB", "payment_method_type": "bank", "payment_method_type_name": "faster_payments"},
        {"country": "GB", "payment_method_type": "bank", "payment_method_type_name": "bacs"},
        
        # BR payment methods
        {"country": "BR", "payment_method_type": "card", "payment_method_type_name": "visa"},
        {"country": "BR", "payment_method_type": "card", "payment_method_type_name": "mastercard"},
        {"country": "BR", "payment_method_type": "bank", "payment_method_type_name": "pix"},
        {"country": "BR", "payment_method_type": "bank", "payment_method_type_name": "ted"},
        
        # DE payment methods
        {"country": "DE", "payment_method_type": "card", "payment_method_type_name": "visa"},
        {"country": "DE", "payment_method_type": "card", "payment_method_type_name": "mastercard"},
        {"country": "DE", "payment_method_type": "bank", "payment_method_type_name": "sepa_credit_transfer"},
        {"country": "DE", "payment_method_type": "bank", "payment_method_type_name": "sepa_direct_debit"},
    ]
    
    return pd.DataFrame(data)


def run_agent(user_input: str) -> Dict[str, Any]:
    """Run the agent with a user input and return the result."""
    graph = build_graph()
    
    initial_state = {
        "messages": [],
        "user_input": user_input,
        "parsed_query": None,
        "result": None
    }
    
    final_state = graph.invoke(initial_state)
    return final_state["result"]



def interactive_mode():
    """
    Run the workflow in interactive mode.
    """
    
    print("🎮 Interactive Mode - Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        user_input = input("\n💬 Enter your message: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            print("⚠️ Please enter a valid message.")
            continue
            
        # Run workflow
        result = run_agent(user_input)
        print(f"Output: {json.dumps(result, indent=2)}")


if __name__ == "__main__":

    interactive_mode()

    print("-" * 30)
