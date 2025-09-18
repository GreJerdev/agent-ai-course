#!/usr/bin/env python3
"""
Test script for payment agent core functions.
This can be run without OpenAI API key to validate the core logic.
"""

from payment_agent import (
    normalize_country_to_alpha2, 
    parse_user_input, 
    query_df, 
    get_demo_dataframe
)

def test_country_normalization():
    """Test country normalization function."""
    print("=== Country Normalization Tests ===")
    test_cases = [
        ("US", "US"),
        ("United States", "US"),
        ("usa", "US"),
        ("UK", "GB"),
        ("Great Britain", "GB"),
        ("united kingdom", "GB"),
        ("GB", "GB"),
        ("BR", "BR"),
        ("brazil", "BR"),
        ("DE", "DE"),
        ("germany", "DE"),
        ("mars", None),
        ("ZZ", None),
        ("", None),
    ]
    
    for input_country, expected in test_cases:
        result = normalize_country_to_alpha2(input_country)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_country}' -> {result} (expected: {expected})")
    
    print()


def test_input_parsing():
    """Test user input parsing function."""
    print("=== Input Parsing Tests ===")
    test_cases = [
        ("US card", "us", "card"),
        ("United Kingdom", "united kingdom", None),
        ("Please list bank methods for br", "br", "bank"),
        ("Germany debit", "germany", "card"),
        ("transfer for GB", "gb", "bank"),
        ("show me visa for usa", "usa", None),  # No explicit card/bank
    ]
    
    for user_input, expected_country, expected_payment_type in test_cases:
        result = parse_user_input(user_input)
        country_match = result.country_text.lower() == expected_country.lower()
        type_match = result.payment_type == expected_payment_type
        status = "✓" if country_match and type_match else "✗"
        print(f"{status} '{user_input}' -> country: '{result.country_text}', type: {result.payment_type}")
        if not country_match or not type_match:
            print(f"    Expected: country: '{expected_country}', type: {expected_payment_type}")
    
    print()


def test_dataframe_queries():
    """Test DataFrame query function."""
    print("=== DataFrame Query Tests ===")
    df = get_demo_dataframe()
    print(f"DataFrame shape: {df.shape}")
    print("Sample data:")
    print(df.head(3))
    print()
    
    test_cases = [
        ("US", "card", ["amex", "mastercard", "visa"]),
        ("US", "bank", ["ach", "wire_transfer"]),
        ("US", None, ["ach", "amex", "mastercard", "visa", "wire_transfer"]),
        ("GB", "card", ["mastercard", "visa"]),
        ("GB", "bank", ["bacs", "faster_payments"]),
        ("BR", "bank", ["pix", "ted"]),
        ("ZZ", "card", []),  # Invalid country
        ("US", "crypto", []),  # Invalid payment type
    ]
    
    for country, payment_type, expected in test_cases:
        result = query_df(country, payment_type, df)
        match = sorted(result) == sorted(expected)
        status = "✓" if match else "✗"
        print(f"{status} query_df('{country}', '{payment_type}') -> {result}")
        if not match:
            print(f"    Expected: {expected}")
    
    print()


def test_end_to_end_logic():
    """Test the complete logic flow without OpenAI."""
    print("=== End-to-End Logic Tests ===")
    df = get_demo_dataframe()
    
    test_cases = [
        "US card",
        "United Kingdom", 
        "Please list bank methods for br",
        "mars card",
    ]
    
    for user_input in test_cases:
        print(f"\nProcessing: '{user_input}'")
        
        # Parse input
        parsed = parse_user_input(user_input)
        print(f"  Parsed country: '{parsed.country_text}', payment_type: {parsed.payment_type}")
        
        # Normalize country
        country_alpha2 = normalize_country_to_alpha2(parsed.country_text)
        print(f"  Normalized country: {country_alpha2}")
        
        # Query DataFrame
        if country_alpha2:
            payment_types = query_df(country_alpha2, parsed.payment_type, df)
            print(f"  Payment types: {payment_types}")
            
            # Simulate final result
            result = {
                "country": country_alpha2,
                "payment_type": parsed.payment_type,
                "count": len(payment_types),
                "types": payment_types,
                "note": "" if payment_types else f"No payment methods found for {country_alpha2}"
            }
        else:
            result = {
                "country": None,
                "payment_type": parsed.payment_type,
                "count": 0,
                "types": [],
                "note": "Invalid country"
            }
        
        print(f"  Final result: {result}")


if __name__ == "__main__":
    print("Payment Agent Function Tests\n")
    print("=" * 50)
    
    test_country_normalization()
    test_input_parsing()
    test_dataframe_queries()
    test_end_to_end_logic()
    
    print("\nAll tests completed!")

