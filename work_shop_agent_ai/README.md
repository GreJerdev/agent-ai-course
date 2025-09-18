# Merchant Analysis AI Agent

An intelligent LangGraph-based agent that analyzes merchant transaction data from BigQuery to identify merchants with unusual transaction patterns, specifically those with high Q50/Average ratios (> 1.5).

## Features

🤖 **AI-Powered Analysis**: Uses LangGraph workflow with OpenAI models  
📊 **BigQuery Integration**: Direct connection to transaction databases  
🔍 **Pattern Detection**: Identifies merchants with Q50/Avg ratio > 1.5  
📈 **Transaction Analysis**: Deep dive into transaction patterns  
🚨 **Anomaly Detection**: Finds outlier transactions causing high ratios  
📋 **Comprehensive Reports**: Detailed insights and recommendations  

## Architecture

The agent uses a multi-step LangGraph workflow:

1. **Data Retrieval**: Get merchant statistics from BigQuery
2. **Filtering**: Identify merchants with Q50/Avg ratio > 1.5  
3. **Detail Analysis**: Fetch detailed transactions for flagged merchants
4. **Pattern Analysis**: Analyze transaction patterns and anomalies
5. **Reporting**: Generate insights and recommendations

## Tools

### 1. Get Merchant Statistics
- **Function**: `get_merchant_statistics`
- **Purpose**: Retrieves aggregated merchant data
- **Outputs**: merchant_id, q50_amount, avg_amount, transaction_count, q50_avg_ratio

### 2. Get Merchant Transactions  
- **Function**: `get_merchant_transactions`
- **Purpose**: Fetches detailed transaction history for specific merchants
- **Outputs**: transaction_id, amount, currency, date, payment_method, etc.

### 3. Analyze Merchant Anomalies
- **Function**: `analyze_merchant_anomalies`
- **Purpose**: Identifies outliers and patterns in transaction data
- **Outputs**: Statistical analysis, anomaly detection, pattern insights

## Installation

1. **Clone or download** the project files

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Copy the example file
   cp env_example.txt .env
   
   # Edit .env with your actual values
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CLOUD_PROJECT=your_gcp_project_id_here
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

4. **Configure BigQuery access**:
   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the file path

## Usage

### Basic Usage

```bash
python main.py
```

### Advanced Usage

```bash
# Specify custom dataset and table
python main.py --dataset my_dataset --table my_transactions

# Analyze last 7 days only
python main.py --days 7

# Use different OpenAI model
python main.py --model gpt-4

# Save results to specific file
python main.py --output results.json

# Enable verbose output
python main.py --verbose
```

### Command Line Options

- `--output, -o`: Output file for results (auto-generated if not specified)
- `--dataset, -d`: BigQuery dataset name (default: transactions_dataset)
- `--table, -t`: BigQuery table name (default: transactions)  
- `--days`: Number of days to analyze (default: 30)
- `--model, -m`: OpenAI model to use (default: gpt-4o-mini)
- `--verbose, -v`: Enable verbose output

## Expected BigQuery Schema

The agent expects a transactions table with these columns:

```sql
CREATE TABLE `project.dataset.transactions` (
  transaction_id STRING,
  merchant_id STRING,
  amount FLOAT64,
  currency STRING,
  transaction_date TIMESTAMP,
  payment_method STRING,
  customer_id STRING,
  status STRING
);
```

## Output

The agent generates a comprehensive JSON report including:

- **Summary statistics**: Total merchants, high-ratio merchants found
- **High-ratio merchants**: List of merchants with Q50/Avg > 1.5
- **Detailed analysis**: Transaction patterns and anomalies
- **Insights**: Common patterns and behavioral insights
- **Recommendations**: Actionable next steps

### Sample Output

```json
{
  "status": "completed",
  "high_ratio_merchants": [
    {
      "merchant_id": "MERCHANT_123",
      "q50_amount": 150.0,
      "avg_amount": 95.5,
      "transaction_count": 1250,
      "q50_avg_ratio": 1.57
    }
  ],
  "analysis_results": [...],
  "configuration": {
    "dataset": "transactions_dataset",
    "analysis_days": 30,
    "execution_time": "2024-01-15T10:30:00"
  }
}
```

## Business Use Cases

- **Risk Assessment**: Identify merchants with unusual transaction patterns
- **Fraud Detection**: Flag potential suspicious activity
- **Business Intelligence**: Understand merchant behavior changes
- **Compliance Monitoring**: Ensure transaction patterns meet regulatory standards
- **Revenue Optimization**: Identify high-value merchant segments

## Key Insights Provided

- **Transaction Distribution Analysis**: Understanding of normal vs. anomalous patterns
- **Outlier Detection**: Identification of transactions causing ratio spikes  
- **Temporal Patterns**: Changes in merchant behavior over time
- **Risk Indicators**: Early warning signs for potential issues
- **Business Recommendations**: Actionable insights for merchant management

## Monitoring Recommendations

1. **Set up automated alerts** for merchants with ratio > 1.5
2. **Investigate large transaction outliers** manually
3. **Consider enhanced verification** for high-ratio merchants  
4. **Monitor ratio trends** over time for significant changes
5. **Regular analysis** to catch emerging patterns early

## Troubleshooting

### Common Issues

1. **BigQuery Authentication**: Ensure service account has BigQuery access
2. **OpenAI API Limits**: Check API quotas and rate limits
3. **Data Schema**: Verify your table matches expected schema
4. **Environment Variables**: Double-check all required variables are set

### Debug Mode

Run with `--verbose` flag to see detailed execution logs:

```bash
python main.py --verbose
```

## Contributing

To extend the agent:

1. **Add new tools** in `bigquery_tools.py`
2. **Modify workflow** in `merchant_analysis_agent.py`
3. **Update analysis logic** as needed
4. **Test with sample data** before production use

## License

This project is designed for internal business use. Please ensure compliance with your organization's data handling policies.
