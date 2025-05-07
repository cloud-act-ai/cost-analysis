#!/bin/bash
# Script to run the FinOps360 dashboard

# Create output directories if they don't exist
mkdir -p reports

# Check if data exists, if not generate it
if [ ! -f "data/cost_analysis_new.csv" ]; then
    echo "Generating sample data..."
    python data/generate_updated_data.py --no-header
fi

# Check if BigQuery is available
if command -v bq &> /dev/null; then
    echo "BigQuery CLI available, checking authentication..."
    
    # Check if user is authenticated
    if bq ls &> /dev/null; then
        echo "BigQuery authenticated, loading data..."
        bash data/load_to_bigquery.sh
        
        echo "Creating BigQuery views..."
        bash data/run_bigquery_views.sh
    else
        echo "BigQuery authentication not available, using local data..."
    fi
else
    echo "BigQuery CLI not available, using local data..."
fi

# Generate the HTML report
echo "Generating HTML dashboard..."
python create_html_report.py

echo "Dashboard generation complete! The report is available in the reports directory."