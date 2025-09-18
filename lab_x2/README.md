# LangGraph Project Skeleton

A complete skeleton for building applications with LangGraph, featuring state management, node implementations, and workflow orchestration.

## Project Structure

```
├── requirements.txt      # Project dependencies
├── state.py             # State definitions and management
├── node.py              # Node implementations
├── main.py              # Main workflow and entry point
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Features

- **Comprehensive State Management**: TypedDict-based state with helper functions
- **Modular Node Architecture**: Separate, reusable node implementations
- **Error Handling**: Built-in error handling and retry mechanisms
- **Conditional Routing**: Dynamic workflow routing based on state
- **Demo and Interactive Modes**: Multiple ways to test and use the workflow
- **Environment Configuration**: Easy setup with environment variables

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Demo

```bash
# Run demo examples
python main.py demo

# Run in interactive mode
python main.py interactive

# Run with direct input
python main.py "Your question here"
```

## Core Components

### State (`state.py`)

Defines the data structures that flow through your graph:

- `GraphState`: Main state for basic workflows
- `WorkflowState`: Extended state for complex scenarios
- Helper functions for state management

### Nodes (`node.py`)

Contains the core business logic:

- `start_node`: Entry point and initialization
- `processing_node`: Main processing logic
- `decision_node`: Routing and decision making
- `finalization_node`: Output preparation and cleanup
- `error_handling_node`: Error management and recovery

### Workflow (`main.py`)

Orchestrates the entire flow:

- Graph construction and configuration
- Edge definitions and conditional routing
- Execution management and error handling
- Demo and interactive modes

## Customization

### Adding New Nodes

1. Define your node function in `node.py`:

```python
def my_custom_node(state: GraphState) -> GraphState:
    # Your logic here
    return updated_state
```

2. Register it in the workflow (`main.py`):

```python
workflow.add_node("my_node", my_custom_node)
workflow.add_edge("previous_node", "my_node")
```

### Extending State

Add new fields to `GraphState` in `state.py`:

```python
class GraphState(TypedDict):
    # Existing fields...
    my_new_field: str
    my_optional_field: Optional[int]
```

### Custom Routing

Create conditional functions for dynamic routing:

```python
def my_routing_function(state: GraphState) -> str:
    if some_condition:
        return "node_a"
    else:
        return "node_b"
```

## Common Patterns

### Sequential Processing
```python
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", "node3")
```

### Conditional Branching
```python
workflow.add_conditional_edges(
    "decision_node",
    routing_function,
    {
        "path_a": "node_a",
        "path_b": "node_b"
    }
)
```

### Error Recovery
```python
workflow.add_conditional_edges(
    "risky_node",
    check_for_errors,
    {
        "success": "next_node",
        "error": "error_handler"
    }
)
```

## Best Practices

1. **State Management**: Keep state minimal and well-typed
2. **Node Design**: Make nodes pure functions when possible
3. **Error Handling**: Always include error handling paths
4. **Testing**: Use demo mode to test different scenarios
5. **Logging**: Include appropriate logging for debugging

## Advanced Features

### LangSmith Integration

Enable tracing by setting environment variables:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=your_project_name
```

### Custom Models

Integrate different LLM providers by modifying the requirements and adding appropriate imports:

```python
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Check your `.env` file configuration
3. **State Type Errors**: Verify your state modifications match the TypedDict definitions

### Debug Mode

Run with debug output:

```bash
DEBUG=true python main.py demo
```

## Contributing

Feel free to extend this skeleton with additional features:

- More sophisticated error handling
- Additional node types
- Performance monitoring
- Database integration
- API endpoints

## License

This project skeleton is provided as-is for educational and development purposes.
