#!/bin/bash
# FinOps360 Cost Analysis Dashboard Runner

# Create output directories if they don't exist
mkdir -p reports

echo "FinOps360 Cost Analysis Dashboard Generator"
echo "-------------------------------------------"

# Check if BigQuery is available
if command -v bq &> /dev/null; then
    echo "BigQuery CLI detected. Checking authentication..."
    
    # Check if user is authenticated
    if bq ls &> /dev/null; then
        echo "BigQuery authenticated!"
        echo "✓ Will attempt to use BigQuery data source"
        # Update config to use BigQuery
        cat > config.yaml << EOF
# FinOps360 Cost Analysis Configuration

# BigQuery settings
bigquery:
  project_id: finops360-dev-2025
  dataset: test
  table: cost_analysis_new
  avg_table: avg_daily_cost_table
  use_bigquery: true
  # credentials: /path/to/credentials.json  # Uncomment and set if needed

# Output settings
output_dir: reports
EOF
    else
        echo "BigQuery CLI found but not authenticated."
        echo "✗ Using sample data instead"
        # Update config to use sample data
        cat > config.yaml << EOF
# FinOps360 Cost Analysis Configuration

# BigQuery settings
bigquery:
  project_id: finops360-dev-2025
  dataset: test
  table: cost_analysis_new
  avg_table: avg_daily_cost_table
  use_bigquery: false

# Output settings
output_dir: reports
EOF
    fi
else
    echo "BigQuery CLI not found on this system."
    echo "✗ Using sample data instead"
    # Update config to use sample data
    cat > config.yaml << EOF
# FinOps360 Cost Analysis Configuration

# BigQuery settings
bigquery:
  project_id: finops360-dev-2025
  dataset: test
  table: cost_analysis_new
  avg_table: avg_daily_cost_table
  use_bigquery: false

# Output settings
output_dir: reports
EOF
fi

# Generate the HTML report
echo ""
echo "Generating HTML dashboard..."
python -m app.main

echo ""
echo "✓ Dashboard generation complete!"
echo "The report is available in the reports directory."