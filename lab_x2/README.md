# Payment Method Query Agent

A Python agent built with OpenAI and LangGraph that queries payment methods from a pandas DataFrame based on country and payment type.

## Features

- **Country Normalization**: Accepts various country formats (ISO codes, full names, common aliases) and normalizes to ISO 3166-1 alpha-2
- **Payment Type Detection**: Automatically detects card/bank payment types with synonym support
- **LangGraph Integration**: Uses a simple graph with LLM parsing and tool execution nodes
- **Structured Output**: Returns consistent JSON format with validation and error handling

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### As a Module

```python
from payment_agent import run_agent

result = run_agent("US card")
print(result)
# Output: {"country": "US", "payment_type": "card", "count": 3, "types": ["amex", "mastercard", "visa"], "note": ""}
```

### Command Line Demo

```bash
python payment_agent.py
```

## DataFrame Schema

The agent expects a pandas DataFrame with these columns:

- `country`: ISO 3166-1 alpha-2 country code (e.g., "US", "GB")
- `payment_method_type`: Payment type ("card" or "bank")
- `payment_method_type_name`: Specific payment method name (e.g., "visa", "ach")

## Example Inputs & Outputs

| Input | Output |
|-------|--------|
| "US card" | Card payment methods for US |
| "United Kingdom" | All payment methods for GB |
| "Please list bank methods for br" | Bank payment methods for Brazil |
| "mars card" | Error for invalid country |

## Key Functions

- `normalize_country_to_alpha2()`: Country name normalization
- `parse_user_input()`: Extract country and payment type from text
- `query_df()`: Filter DataFrame and return matching payment methods
- `build_graph()`: Create LangGraph workflow
- `run_agent()`: Execute the full agent pipeline

## Error Handling

The agent handles various error cases gracefully:
- Invalid country names
- Missing countries
- Empty results
- API failures

All errors return valid JSON with empty `types` list and descriptive `note` field.

