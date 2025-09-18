"""
Main execution script for the Merchant Analysis AI Agent.

This script runs the complete workflow to:
1. Fetch merchant statistics from BigQuery
2. Identify merchants with q50/avg ratio > 1.5
3. Analyze their transaction patterns
4. Provide insights and recommendations
"""

import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

from merchant_analysis_agent import create_merchant_analysis_agent


def setup_environment():
    """Setup environment variables and configuration."""
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        print("- OPENAI_API_KEY: Your OpenAI API key")
        print("- GOOGLE_CLOUD_PROJECT: Your Google Cloud project ID")
        print("\nYou can set them in a .env file or as environment variables.")
        return False
    
    print("✅ Environment setup complete")
    return True


def save_results(results: dict, output_file: str = None):
    """Save analysis results to a JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"merchant_analysis_results_{timestamp}.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📊 Results saved to: {output_file}")
    return output_file


def print_summary(results: dict):
    """Print a summary of the analysis results."""
    print("\n" + "="*80)
    print("🏪 MERCHANT ANALYSIS SUMMARY")
    print("="*80)
    
    high_ratio_merchants = results.get("high_ratio_merchants", [])
    
    if not high_ratio_merchants:
        print("❌ No merchants found with q50/avg ratio > 1.5")
        return
    
    print(f"✅ Found {len(high_ratio_merchants)} merchants with q50/avg ratio > 1.5\n")
    
    print("📈 HIGH-RATIO MERCHANTS:")
    print("-" * 50)
    
    for i, merchant in enumerate(high_ratio_merchants[:10], 1):  # Show top 10
        merchant_id = merchant.get("merchant_id", "N/A")
        ratio = merchant.get("q50_avg_ratio", 0)
        tx_count = merchant.get("transaction_count", 0)
        avg_amount = merchant.get("avg_amount", 0)
        q50_amount = merchant.get("q50_amount", 0)
        
        print(f"{i:2d}. Merchant: {merchant_id}")
        print(f"    Q50/Avg Ratio: {ratio:.3f}")
        print(f"    Transactions: {tx_count:,}")
        print(f"    Avg Amount: ${avg_amount:,.2f}")
        print(f"    Q50 Amount: ${q50_amount:,.2f}")
        print()
    
    print("🔍 KEY INSIGHTS:")
    print("-" * 50)
    print("• High q50/avg ratios indicate transaction distributions skewed toward higher values")
    print("• This could suggest premium customer segments or business model changes")
    print("• Outlier transactions may be driving unusual patterns")
    print("• These merchants warrant closer monitoring for risk assessment")
    
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 50)
    print("• Set up automated alerts for merchants with ratio > 1.5")
    print("• Investigate large transaction outliers manually")
    print("• Consider enhanced verification for high-ratio merchants")
    print("• Monitor ratio trends over time for significant changes")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run Merchant Analysis AI Agent")
    parser.add_argument(
        "--output", 
        "-o", 
        type=str, 
        help="Output file for results (default: auto-generated)"
    )
    parser.add_argument(
        "--dataset", 
        "-d", 
        type=str, 
        default="transactions_dataset",
        help="BigQuery dataset name (default: transactions_dataset)"
    )
    parser.add_argument(
        "--table", 
        "-t", 
        type=str, 
        default="transactions",
        help="BigQuery table name (default: transactions)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    parser.add_argument(
        "--model", 
        "-m", 
        type=str, 
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    print("🤖 Merchant Analysis AI Agent")
    print("="*50)
    
    # Setup environment
    if not setup_environment():
        return 1
    
    try:
        # Create and configure the agent
        print("🚀 Initializing AI agent...")
        agent = create_merchant_analysis_agent(model_name=args.model)
        
        print(f"📊 Starting analysis...")
        print(f"   Dataset: {args.dataset}")
        print(f"   Table: {args.table}")
        print(f"   Analysis period: {args.days} days")
        print(f"   Model: {args.model}")
        
        # Run the analysis
        config = {
            "configurable": {
                "thread_id": f"merchant_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        results = agent.run_analysis(config=config)
        
        # Add configuration to results
        results["configuration"] = {
            "dataset": args.dataset,
            "table": args.table,
            "analysis_days": args.days,
            "model": args.model,
            "execution_time": datetime.now().isoformat()
        }
        
        # Save results
        output_file = save_results(results, args.output)
        
        # Print summary
        print_summary(results)
        
        if args.verbose:
            print("\n📝 DETAILED MESSAGES:")
            print("-" * 50)
            for i, msg in enumerate(results.get("messages", []), 1):
                print(f"{i:2d}. {msg}")
                print()
        
        print(f"\n✅ Analysis complete! Results saved to: {output_file}")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
