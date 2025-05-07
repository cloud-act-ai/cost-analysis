#!/bin/bash
# FinOps360 Cost Analysis Dashboard Runner

# Parse command line arguments
PROJECT_ID="finops360-dev-2025"
DATASET="test"
OUTPUT_DIR="reports"

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift ;;
        --dataset) DATASET="$2"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift ;;
        *) APP_ARGS+=("$1") ;;
    esac
    shift
done

# Create output directories if they don't exist
mkdir -p "$OUTPUT_DIR"

echo "FinOps360 Cost Analysis Dashboard Generator"
echo "-------------------------------------------"
echo "Project ID: $PROJECT_ID"
echo "Dataset: $DATASET"
echo "Output directory: $OUTPUT_DIR"

# Check if BigQuery is available
if command -v bq &> /dev/null; then
    echo "BigQuery CLI detected. Checking authentication..."
    
    # Check if user is authenticated
    if bq ls &> /dev/null; then
        echo "BigQuery authenticated!"
        echo "✓ Will use BigQuery data source"
    else
        echo "Warning: BigQuery CLI found but not authenticated."
        echo "  Will still attempt to use BigQuery but may fail"
    fi
else
    echo "Warning: BigQuery CLI not found on this system."
    echo "  Will still attempt to use BigQuery but may fail"
fi

# Always use BigQuery
cat > config.yaml << EOF
# FinOps360 Cost Analysis Configuration

# BigQuery settings
bigquery:
  project_id: ${PROJECT_ID}
  dataset: ${DATASET}
  table: cost_analysis_new
  avg_table: avg_daily_cost_table
  use_bigquery: true
  # credentials: /path/to/credentials.json  # Uncomment and set if needed

# Dashboard settings
interactive_charts: true

# Output settings
output_dir: ${OUTPUT_DIR}
EOF

# Generate the HTML report
echo ""
echo "Generating HTML dashboard..."

# Check if Plotly is installed
if python -c "import plotly" 2>/dev/null; then
    echo "✓ Interactive charts enabled (Plotly detected)"
else
    echo "! Interactive charts not available (Plotly not installed)"
    echo "  To enable interactive charts, run: pip install plotly>=5.14.0"
fi

# Run the application
python -m app.main "${APP_ARGS[@]}"

echo ""
echo "✓ Dashboard generation complete!"
echo "The report is available in the reports directory."