#!/usr/bin/env python3
"""
Simple validation script to check imports and basic functionality.
"""

print("Validating payment agent setup...")

try:
    import pandas as pd
    print("✓ pandas imported successfully")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")

try:
    import pycountry
    print("✓ pycountry imported successfully")
except ImportError as e:
    print(f"✗ pycountry import failed: {e}")

try:
    from langgraph.graph import StateGraph, END
    print("✓ langgraph imported successfully")
except ImportError as e:
    print(f"✗ langgraph import failed: {e}")

try:
    from openai import OpenAI
    print("✓ openai imported successfully")
except ImportError as e:
    print(f"✗ openai import failed: {e}")

# Test basic functionality without full agent
try:
    from payment_agent import normalize_country_to_alpha2, get_demo_dataframe
    
    # Test country normalization
    test_result = normalize_country_to_alpha2("US")
    assert test_result == "US", f"Expected 'US', got {test_result}"
    print("✓ Country normalization working")
    
    # Test DataFrame creation
    df = get_demo_dataframe()
    assert not df.empty, "DataFrame should not be empty"
    assert len(df) > 0, "DataFrame should have rows"
    print(f"✓ Demo DataFrame created with {len(df)} rows")
    
    print("\n✓ Basic validation passed! The payment agent should work correctly.")
    
except Exception as e:
    print(f"✗ Validation failed: {e}")

print("\nTo run the full agent, ensure you have OPENAI_API_KEY set and run:")
print("python3 payment_agent.py")
