"""
Demo script for the Merchant Analysis AI Agent.

This script demonstrates how to use the agent programmatically
and provides sample data for testing without requiring actual BigQuery setup.
"""

import json
import os
from datetime import datetime, timedelta
import pandas as pd
from merchant_analysis_agent import create_merchant_analysis_agent


def create_sample_data():
    """Create sample merchant transaction data for demonstration."""
    
    # Sample merchant statistics data
    sample_merchants = [
        {
            "merchant_id": "MERCHANT_001",
            "q50_amount": 150.0,
            "avg_amount": 95.5,
            "transaction_count": 1250,
            "q50_avg_ratio": 1.57
        },
        {
            "merchant_id": "MERCHANT_002", 
            "q50_amount": 75.0,
            "avg_amount": 80.2,
            "transaction_count": 890,
            "q50_avg_ratio": 0.94
        },
        {
            "merchant_id": "MERCHANT_003",
            "q50_amount": 200.0,
            "avg_amount": 125.8,
            "transaction_count": 2100,
            "q50_avg_ratio": 1.59
        },
        {
            "merchant_id": "MERCHANT_004",
            "q50_amount": 300.0,
            "avg_amount": 180.5,
            "transaction_count": 450,
            "q50_avg_ratio": 1.66
        },
        {
            "merchant_id": "MERCHANT_005",
            "q50_amount": 50.0,
            "avg_amount": 65.3,
            "transaction_count": 1800,
            "q50_avg_ratio": 0.77
        }
    ]
    
    # Sample transaction data for high-ratio merchants
    sample_transactions = {
        "MERCHANT_001": [
            {"transaction_id": "TXN_001_001", "amount": 25.0, "currency": "USD", "transaction_date": "2024-01-10 09:15:00"},
            {"transaction_id": "TXN_001_002", "amount": 150.0, "currency": "USD", "transaction_date": "2024-01-10 10:30:00"}, 
            {"transaction_id": "TXN_001_003", "amount": 175.0, "currency": "USD", "transaction_date": "2024-01-10 11:45:00"},
            {"transaction_id": "TXN_001_004", "amount": 500.0, "currency": "USD", "transaction_date": "2024-01-10 14:20:00"},  # Outlier
            {"transaction_id": "TXN_001_005", "amount": 125.0, "currency": "USD", "transaction_date": "2024-01-11 08:10:00"},
            {"transaction_id": "TXN_001_006", "amount": 180.0, "currency": "USD", "transaction_date": "2024-01-11 12:30:00"},
            {"transaction_id": "TXN_001_007", "amount": 45.0, "currency": "USD", "transaction_date": "2024-01-12 09:00:00"},
            {"transaction_id": "TXN_001_008", "amount": 220.0, "currency": "USD", "transaction_date": "2024-01-12 15:45:00"},
            {"transaction_id": "TXN_001_009", "amount": 160.0, "currency": "USD", "transaction_date": "2024-01-13 10:15:00"},
            {"transaction_id": "TXN_001_010", "amount": 800.0, "currency": "USD", "transaction_date": "2024-01-13 16:30:00"}   # Large outlier
        ],
        "MERCHANT_003": [
            {"transaction_id": "TXN_003_001", "amount": 180.0, "currency": "USD", "transaction_date": "2024-01-10 08:00:00"},
            {"transaction_id": "TXN_003_002", "amount": 220.0, "currency": "USD", "transaction_date": "2024-01-10 10:15:00"},
            {"transaction_id": "TXN_003_003", "amount": 195.0, "currency": "USD", "transaction_date": "2024-01-10 14:30:00"},
            {"transaction_id": "TXN_003_004", "amount": 1200.0, "currency": "USD", "transaction_date": "2024-01-11 09:45:00"},  # Large outlier
            {"transaction_id": "TXN_003_005", "amount": 160.0, "currency": "USD", "transaction_date": "2024-01-11 11:20:00"},
            {"transaction_id": "TXN_003_006", "amount": 240.0, "currency": "USD", "transaction_date": "2024-01-12 13:10:00"},
            {"transaction_id": "TXN_003_007", "amount": 30.0, "currency": "USD", "transaction_date": "2024-01-12 16:45:00"},   # Small outlier
            {"transaction_id": "TXN_003_008", "amount": 210.0, "currency": "USD", "transaction_date": "2024-01-13 08:30:00"},
            {"transaction_id": "TXN_003_009", "amount": 185.0, "currency": "USD", "transaction_date": "2024-01-13 12:00:00"},
            {"transaction_id": "TXN_003_010", "amount": 950.0, "currency": "USD", "transaction_date": "2024-01-14 15:20:00"}   # Another large outlier
        ],
        "MERCHANT_004": [
            {"transaction_id": "TXN_004_001", "amount": 280.0, "currency": "USD", "transaction_date": "2024-01-10 09:30:00"},
            {"transaction_id": "TXN_004_002", "amount": 320.0, "currency": "USD", "transaction_date": "2024-01-10 11:00:00"},
            {"transaction_id": "TXN_004_003", "amount": 290.0, "currency": "USD", "transaction_date": "2024-01-11 10:15:00"},
            {"transaction_id": "TXN_004_004", "amount": 310.0, "currency": "USD", "transaction_date": "2024-01-11 14:45:00"},
            {"transaction_id": "TXN_004_005", "amount": 15.0, "currency": "USD", "transaction_date": "2024-01-12 08:20:00"},   # Small outlier
            {"transaction_id": "TXN_004_006", "amount": 305.0, "currency": "USD", "transaction_date": "2024-01-12 12:30:00"},
            {"transaction_id": "TXN_004_007", "amount": 295.0, "currency": "USD", "transaction_date": "2024-01-13 09:10:00"},
            {"transaction_id": "TXN_004_008", "amount": 25.0, "currency": "USD", "transaction_date": "2024-01-13 13:45:00"},   # Small outlier
            {"transaction_id": "TXN_004_009", "amount": 285.0, "currency": "USD", "transaction_date": "2024-01-14 10:00:00"},
            {"transaction_id": "TXN_004_010", "amount": 330.0, "currency": "USD", "transaction_date": "2024-01-14 16:20:00"}
        ]
    }
    
    return sample_merchants, sample_transactions


def demo_agent_workflow():
    """Demonstrate the agent workflow with sample data."""
    
    print("🤖 Merchant Analysis AI Agent - Demo Mode")
    print("="*60)
    
    # Check if we have OpenAI API key (required even for demo)
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is required")
        print("   Please set your OpenAI API key to run the demo")
        return
    
    print("📊 Creating sample merchant data...")
    sample_merchants, sample_transactions = create_sample_data()
    
    print(f"   - {len(sample_merchants)} sample merchants")
    print(f"   - {sum(len(txns) for txns in sample_transactions.values())} sample transactions")
    
    # Filter high-ratio merchants (q50/avg > 1.5)
    high_ratio_merchants = [m for m in sample_merchants if m["q50_avg_ratio"] > 1.5]
    print(f"   - {len(high_ratio_merchants)} merchants with q50/avg > 1.5")
    
    print("\n🔍 High-Ratio Merchants Found:")
    print("-" * 40)
    for merchant in high_ratio_merchants:
        print(f"   {merchant['merchant_id']}: ratio = {merchant['q50_avg_ratio']:.2f}")
    
    print("\n📈 Sample Transaction Analysis:")
    print("-" * 40)
    
    for merchant_id in ["MERCHANT_001", "MERCHANT_003", "MERCHANT_004"]:
        if merchant_id in sample_transactions:
            transactions = sample_transactions[merchant_id]
            amounts = [t["amount"] for t in transactions]
            
            print(f"\n{merchant_id}:")
            print(f"   Transactions: {len(transactions)}")
            print(f"   Amount range: ${min(amounts):.2f} - ${max(amounts):.2f}")
            print(f"   Average: ${sum(amounts)/len(amounts):.2f}")
            print(f"   Median: ${sorted(amounts)[len(amounts)//2]:.2f}")
            
            # Identify outliers
            q75 = sorted(amounts)[3*len(amounts)//4]
            q25 = sorted(amounts)[len(amounts)//4]
            iqr = q75 - q25
            upper_bound = q75 + 1.5 * iqr
            lower_bound = q25 - 1.5 * iqr
            
            outliers = [t for t in transactions if t["amount"] > upper_bound or t["amount"] < lower_bound]
            if outliers:
                print(f"   Outliers found: {len(outliers)}")
                for outlier in outliers:
                    print(f"     - ${outlier['amount']:.2f} on {outlier['transaction_date']}")
    
    print("\n💡 Demo Insights:")
    print("-" * 40)
    print("• MERCHANT_001: Has outlier transactions (500, 800) skewing the distribution")
    print("• MERCHANT_003: Large transactions (1200, 950) indicate premium customers")  
    print("• MERCHANT_004: Small outliers (15, 25) suggest refunds or fees")
    print("• All high-ratio merchants show bimodal or skewed distributions")
    
    print("\n🚨 Recommended Actions:")
    print("-" * 40)
    print("• Investigate large transactions for legitimacy")
    print("• Set up alerts for transactions > $500")
    print("• Consider enhanced verification for these merchants")
    print("• Monitor ratio trends for sudden changes")
    
    print("\n✅ Demo completed! This shows how the agent would analyze real BigQuery data.")
    print("   To run with live data, configure BigQuery credentials and run: python main.py")


def demo_programmatic_usage():
    """Demonstrate how to use the agent programmatically."""
    
    print("\n" + "="*60)
    print("🔧 Programmatic Usage Example")
    print("="*60)
    
    print("""
# Example: Using the agent in your own code

from merchant_analysis_agent import create_merchant_analysis_agent

# Create agent instance
agent = create_merchant_analysis_agent(model_name="gpt-4o-mini")

# Configure analysis
config = {
    "configurable": {
        "thread_id": "my_analysis_session"
    }
}

# Run analysis
results = agent.run_analysis(config=config)

# Access results
high_ratio_merchants = results["high_ratio_merchants"]
analysis_details = results["analysis_results"] 

# Process results
for merchant in high_ratio_merchants:
    if merchant["q50_avg_ratio"] > 2.0:  # Very high ratio
        print(f"ALERT: {merchant['merchant_id']} has extreme ratio")

# Save results
import json
with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)
""")


if __name__ == "__main__":
    # Run the demo
    demo_agent_workflow()
    demo_programmatic_usage()
