from dotenv import load_dotenv
import os
import json
from typing import Dict, Any
from openai import OpenAI
import math

load_dotenv(override=True)

# Check the key
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print(
        "OpenAI API Key not set - please head to the troubleshooting guide in the setup folder"
    )


def init_openai():
    """Initialize OpenAI client"""
    return OpenAI(api_key=openai_api_key)


# Define tools that the agent can use
def get_weather_tool(location: str) -> Dict[str, Any]:
    """
    Get current weather for a location.
    Note: This is a mock function. In a real implementation, you'd use a weather API.
    """
    # Mock weather data for demonstration
    mock_weather_data = {
        "new york": {"temperature": 22, "condition": "sunny", "humidity": 65},
        "london": {"temperature": 15, "condition": "cloudy", "humidity": 80},
        "tokyo": {"temperature": 28, "condition": "rainy", "humidity": 75},
        "paris": {"temperature": 18, "condition": "partly cloudy", "humidity": 70},
    }
    
    location_key = location.lower().strip()
    weather = mock_weather_data.get(location_key, {"temperature": 20, "condition": "unknown", "humidity": 50})
    
    return {
        "location": location,
        "temperature": weather["temperature"],
        "condition": weather["condition"],
        "humidity": weather["humidity"]
    }


def calculator_tool(operation: str, a: float, b: float = None) -> Dict[str, Any]:
    """
    Perform mathematical calculations.
    """
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {"error": "Division by zero is not allowed"}
            result = a / b
        elif operation == "power":
            result = a ** b
        elif operation == "sqrt":
            result = math.sqrt(a)
        elif operation == "sin":
            result = math.sin(math.radians(a))
        elif operation == "cos":
            result = math.cos(math.radians(a))
        elif operation == "tan":
            result = math.tan(math.radians(a))
        else:
            return {"error": f"Unknown operation: {operation}"}
        
        return {
            "operation": operation,
            "operands": [a, b] if b is not None else [a],
            "result": result
        }
    except Exception as e:
        return {"error": str(e)}


def web_search_tool(query: str) -> Dict[str, Any]:
    """
    Perform web search.
    Note: This is a mock function. In a real implementation, you'd use a search API.
    """
    # Mock search results for demonstration
    mock_results = {
        "python": [
            {"title": "Python Programming Language", "url": "https://python.org", "snippet": "Python is a high-level programming language..."},
            {"title": "Python Tutorial", "url": "https://docs.python.org/tutorial", "snippet": "Learn Python programming with our comprehensive tutorial..."}
        ],
        "ai": [
            {"title": "Artificial Intelligence", "url": "https://en.wikipedia.org/wiki/Artificial_intelligence", "snippet": "AI is intelligence demonstrated by machines..."},
            {"title": "Machine Learning", "url": "https://en.wikipedia.org/wiki/Machine_learning", "snippet": "Machine learning is a subset of AI..."}
        ],
        "weather": [
            {"title": "Weather Forecast", "url": "https://weather.com", "snippet": "Get current weather conditions and forecasts..."}
        ]
    }
    
    query_key = query.lower().strip()
    results = mock_results.get(query_key, [
        {"title": f"Search results for {query}", "url": "https://example.com", "snippet": f"Information about {query}..."}
    ])
    
    return {
        "query": query,
        "results": results[:3]  # Return top 3 results
    }


def get_current_time_tool() -> Dict[str, Any]:
    """
    Get current time.
    """
    import datetime
    now = datetime.datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "UTC",
        "timestamp": now.timestamp()
    }


# Define the tools schema for OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_tool",
            "description": "Get current weather information for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location to get weather for"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator_tool",
            "description": "Perform mathematical calculations including basic operations and trigonometric functions",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt", "sin", "cos", "tan"],
                        "description": "The mathematical operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number for the operation"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number for the operation (not needed for sqrt, sin, cos, tan)"
                    }
                },
                "required": ["operation", "a"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search_tool",
            "description": "Search the web for information on a given topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time_tool",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# Tool execution function
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool function based on the tool name and arguments"""
    if tool_name == "get_weather_tool":
        return get_weather_tool(**arguments)
    elif tool_name == "calculator_tool":
        return calculator_tool(**arguments)
    elif tool_name == "web_search_tool":
        return web_search_tool(**arguments)
    elif tool_name == "get_current_time_tool":
        return get_current_time_tool()
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_agent_conversation(client: OpenAI, user_message: str) -> str:
    """Run a conversation with the agent using tools"""
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant with access to various tools. You can help with weather information, calculations, web searches, and time queries. Always use the appropriate tool when needed and provide clear, helpful responses."
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # First API call to get tool calls
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=1000
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    # Check if the model wants to call a tool
    if response_message.tool_calls:
        print("\n🔧 Agent is using tools...")
        
        # Execute each tool call
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"   Using tool: {tool_name}")
            print(f"   Arguments: {tool_args}")
            
            # Execute the tool
            tool_result = execute_tool(tool_name, tool_args)
            
            print(f"   Result: {tool_result}")
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })
        
        # Second API call to get the final response
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return second_response.choices[0].message.content
    else:
        return response_message.content


def main():
    """Main function to demonstrate the agent with tools"""
    client = init_openai()
    
    print("🤖 OpenAI Agent with Tools Demo")
    print("=" * 50)
    print("Available tools:")
    print("- Weather information")
    print("- Mathematical calculations")
    print("- Web search")
    print("- Current time")
    print("=" * 50)
    
    # Example conversations
    examples = [
        "What's the weather like in New York?",
        "Calculate 15 * 23 + 45",
        "What's the square root of 144?",
        "Search for information about Python programming",
        "What time is it now?",
        "What's the weather in Tokyo and calculate the temperature in Fahrenheit if it's 28°C?"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Example {i}: {example}")
        print("-" * 50)
        
        try:
            response = run_agent_conversation(client, example)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    # Interactive mode
    print("\n🎯 Interactive Mode - Ask me anything!")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if user_input:
                response = run_agent_conversation(client, user_input)
                print(f"🤖 Agent: {response}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
