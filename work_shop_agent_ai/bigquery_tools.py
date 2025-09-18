"""
BigQuery tools for merchant analysis agent.
Provides tools to:
1. Get merchant statistics (q50, avg, transaction count)
2. Get detailed transactions for specific merchants
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery
from langchain.tools import tool
import json


class BigQueryClient:
    """BigQuery client wrapper for merchant analysis."""
    
    def __init__(self, project_id: str = None):
        """Initialize BigQuery client."""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.client = bigquery.Client(project=self.project_id)
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a BigQuery query and return results as DataFrame."""
        try:
            query_job = self.client.query(query)
            return query_job.to_dataframe()
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()


# Global BigQuery client instance
bq_client = BigQueryClient()


@tool
def get_merchant_statistics(
    dataset_name: str = "transactions_dataset",
    table_name: str = "transactions",
    days_back: int = 30
) -> str:
    """
    Get list of merchants with their statistics including q50 amount, avg amount, and number of transactions.
    
    Args:
        dataset_name: BigQuery dataset name (default: transactions_dataset)
        table_name: BigQuery table name (default: transactions)
        days_back: Number of days to look back for analysis (default: 30)
    
    Returns:
        JSON string containing merchant statistics with columns:
        - merchant_id: Unique merchant identifier
        - q50_amount: Median (50th percentile) transaction amount
        - avg_amount: Average transaction amount
        - transaction_count: Total number of transactions
        - q50_avg_ratio: Ratio of q50/avg for quick filtering
    """
    
    query = f"""
    WITH merchant_stats AS (
        SELECT 
            trx.merchant_table_id,
            COUNT(*) as transaction_count,
            AVG(transaction_amount_usd) as avg_amount,
             
            APPROX_QUANTILES(ABS(transaction_amount_usd), 100)[OFFSET(50)] q50_amount,
        FROM  `rapyd-valitor-data.valitor_main.main_fact_transactions` trx
        WHERE DATE(trx.transaction_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
          AND transaction_amount_usd > 0
          and transaction_is_ecom = True
        GROUP BY merchant_table_id
    )
    SELECT 
        merchant_table_id,
        q50_amount,
        avg_amount,
        transaction_count,
        ROUND(q50_amount / NULLIF(avg_amount, 0), 3) as q50_avg_ratio
    FROM merchant_stats
    WHERE avg_amount > 0
    ORDER BY q50_avg_ratio DESC, transaction_count DESC
    LIMIT 50;
    """
    
    try:
        df = bq_client.execute_query(query)
        if df.empty:
            return json.dumps({
                "error": "No merchant data found",
                "merchants": []
            })
        
        # Convert to list of dictionaries for JSON serialization
        merchants = df.to_dict('records')
        
        result = {
            "total_merchants": len(merchants),
            "merchants": merchants,
            "query_period_days": days_back
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch merchant statistics: {str(e)}",
            "merchants": []
        })


@tool
def get_merchant_transactions(
    merchant_id: str,
    dataset_name: str = "transactions_dataset", 
    table_name: str = "transactions",
    days_back: int = 7
) -> str:
    """
    Get detailed transactions for a specific merchant for the last 7 days (or specified period).
    
    Args:
        merchant_id: The merchant ID to get transactions for
        dataset_name: BigQuery dataset name (default: transactions_dataset)
        table_name: BigQuery table name (default: transactions) 
        days_back: Number of days to look back (default: 7)
    
    Returns:
        JSON string containing transaction details with columns:
        - transaction_id: Unique transaction identifier
        - merchant_id: Merchant identifier
        - amount: Transaction amount
        - currency: Transaction currency
        - transaction_date: Date and time of transaction
        - additional transaction metadata if available
    """
    
    query = f"""
    SELECT 
        transaction_id_fk as transaction_id,
        trx.merchant_table_id as merchant_id,
        transaction_amount_usd as amount,
        transaction_currency_code as currency,
        transaction_date
    FROM  `rapyd-valitor-data.valitor_main.main_fact_transactions` trx
        WHERE DATE(trx.transaction_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
      AND trx.merchant_table_id = '{merchant_id}'
      AND transaction_type_code = "SALE05"
      AND amount > 0
    ORDER BY transaction_date DESC
    LIMIT 50000
    """
    
    try:
        df = bq_client.execute_query(query)
        if df.empty:
            return json.dumps({
                "error": f"No transactions found for merchant {merchant_id}",
                "merchant_id": merchant_id,
                "transactions": []
            })
        
        # Convert datetime objects to strings for JSON serialization
        if 'transaction_date' in df.columns:
            df['transaction_date'] = df['transaction_date'].astype(str)
        
        transactions = df.to_dict('records')
        
        # Calculate summary statistics
        amounts = df['amount'].tolist()
        
        result = {
            "merchant_id": merchant_id,
            "query_period_days": days_back,
            "total_transactions": len(transactions),
            "transaction_summary": {
                "total_amount": sum(amounts),
                "avg_amount": sum(amounts) / len(amounts) if amounts else 0,
                "min_amount": min(amounts) if amounts else 0,
                "max_amount": max(amounts) if amounts else 0,
                "q50_amount": sorted(amounts)[len(amounts)//2] if amounts else 0
            },
            "transactions": transactions
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch transactions for merchant {merchant_id}: {str(e)}",
            "merchant_id": merchant_id,
            "transactions": []
        })


@tool 
def analyze_merchant_anomalies(merchant_data: str) -> str:
    """
    Analyze merchant data to identify anomalous transactions that contribute to high q50/avg ratios.
    
    Args:
        merchant_data: JSON string containing merchant transaction data from get_merchant_transactions
    
    Returns:
        JSON string with analysis of potential anomalies and patterns
    """
    
    try:
        data = json.loads(merchant_data)
        
        if "error" in data or not data.get("transactions"):
            return json.dumps({
                "error": "No valid transaction data provided for analysis",
                "analysis": {}
            })
        
        transactions = data["transactions"]
        amounts = [float(t["amount"]) for t in transactions if t.get("amount")]
        
        if not amounts:
            return json.dumps({
                "error": "No valid amounts found in transaction data",
                "analysis": {}
            })
        
        # Calculate statistics
        amounts_sorted = sorted(amounts)
        n = len(amounts_sorted)
        q25 = amounts_sorted[n//4] if n > 0 else 0
        q50 = amounts_sorted[n//2] if n > 0 else 0
        q75 = amounts_sorted[3*n//4] if n > 0 else 0
        avg_amount = sum(amounts) / len(amounts)
        
        # Identify potential anomalies using IQR method
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        anomalies = []
        large_transactions = []
        
        for tx in transactions:
            amount = float(tx.get("amount", 0))
            if amount < lower_bound or amount > upper_bound:
                anomalies.append({
                    "transaction_id": tx.get("transaction_id"),
                    "amount": amount,
                    "date": tx.get("transaction_date"),
                    "type": "outlier",
                    "reason": f"Amount {amount} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
                })
            
            if amount > q75 * 2:  # Transactions significantly larger than Q75
                large_transactions.append({
                    "transaction_id": tx.get("transaction_id"),
                    "amount": amount,
                    "date": tx.get("transaction_date"),
                    "multiple_of_q75": round(amount / q75, 2) if q75 > 0 else 0
                })
        
        # Analyze what drives the high q50/avg ratio
        q50_avg_ratio = q50 / avg_amount if avg_amount > 0 else 0
        
        analysis = {
            "merchant_id": data.get("merchant_id"),
            "q50_avg_ratio": round(q50_avg_ratio, 3),
            "statistics": {
                "q25": round(q25, 2),
                "q50": round(q50, 2), 
                "q75": round(q75, 2),
                "avg": round(avg_amount, 2),
                "min": round(min(amounts), 2),
                "max": round(max(amounts), 2)
            },
            "anomaly_analysis": {
                "total_anomalies": len(anomalies),
                "anomalous_transactions": anomalies[:10],  # Limit to first 10
                "large_transactions": large_transactions[:10]
            },
            "ratio_explanation": {
                "high_ratio_indicates": "Many transactions are at or above median, suggesting consistent higher-value transactions",
                "potential_causes": [
                    "Bimodal distribution with many small and large transactions",
                    "Recent shift towards higher value transactions", 
                    "Outlier transactions skewing the average downward relative to median",
                    "Business model changes or customer behavior shifts"
                ]
            }
        }
        
        return json.dumps(analysis, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to analyze merchant anomalies: {str(e)}",
            "analysis": {}
        })


# List of available tools for the agent
BIGQUERY_TOOLS = [
    get_merchant_statistics,
    get_merchant_transactions, 
    analyze_merchant_anomalies
]
