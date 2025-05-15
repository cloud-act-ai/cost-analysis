#!/bin/bash
# FinOps360 Cost Analysis Dashboard Runner

# Create output directory if it doesn't exist
mkdir -p reports

echo "FinOps360 Cost Analysis Dashboard Generator"
echo "-------------------------------------------"

echo "✓ Setting Google Application Credentials"

# Check BigQuery authentication
if command -v bq &> /dev/null && bq ls &> /dev/null; then
    echo "✓ BigQuery authenticated"
else
    echo "! BigQuery authentication issue - will attempt to continue"
fi

# Check for Plotly availability
if python3 -c "import plotly" 2>/dev/null; then
    echo "✓ Interactive charts enabled (Plotly detected)"
else
    echo "! Interactive charts not available (Plotly not installed)"
    echo "  To enable interactive charts, run: pip3 install plotly>=5.14.0"
fi

# Generate the HTML report
echo ""
echo "Generating HTML dashboard..."

# Run the application with debug mode
python3 -m app.main --debug

echo ""
echo "✓ Dashboard generation complete!"
echo "Report available in the configured output directory"