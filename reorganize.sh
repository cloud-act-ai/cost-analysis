#!/bin/bash

echo "FinOps360 Cost Analysis - Project Reorganization"
echo "----------------------------------------------"

# Create new structure
echo "Creating new directory structure..."
mkdir -p app/core
mkdir -p app/api
mkdir -p app/models
mkdir -p app/services
mkdir -p app/templates
mkdir -p app/static
mkdir -p app/config
mkdir -p app/utils
mkdir -p app/sql

# Move files to their new locations
echo "Moving files to new locations..."

# Move FastAPI app files to core
mv app/fastapi_app.py app/core/app.py
mv app/fastapi_dashboard.py app/core/dashboard.py
mv app/fastapi_data_access.py app/core/data_access.py

# Move utils
mkdir -p app/utils/chart
mv app/utils/chart_config.py app/utils/chart/config.py
mv app/utils/interactive_charts.py app/utils/chart/generator.py
mv app/utils/sample_data.py app/utils/data_generator.py
mv app/utils/bigquery.py app/utils/db.py
mv app/utils/config.py app/utils/config_loader.py

# Move config file
mv config.yaml app/config/config.yaml

# Create symlink for compatibility
ln -sf app/config/config.yaml ./config.yaml

# Move requirements.txt
mv requirements.txt app/config/requirements.txt
ln -sf app/config/requirements.txt ./requirements.txt

# Move templates
mv app/templates/* app/templates/
rmdir app/templates 2>/dev/null || true

# Create main entry point
echo "Creating main entry point..."
cat > app/__main__.py << 'EOF'
"""
FinOps360 Cost Analysis - Main Entry Point
Run with: python -m app
"""
import uvicorn
import os
import sys
import argparse


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="FinOps360 Cost Analysis Dashboard")
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to run the server on (default: 8080)"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--workers", type=int, default=None, 
        help="Number of worker processes (default: based on CPU count)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Set default workers based on CPU count
    if args.workers is None:
        import multiprocessing
        args.workers = min(multiprocessing.cpu_count(), 4)  # Cap at 4 workers
    
    # Print information
    print(f"FinOps360 Cost Analysis Dashboard")
    print(f"----------------------------------")
    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"Workers: {args.workers}")
    print(f"Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    print()
    
    # Run the server
    uvicorn.run(
        "app.core.app:app", 
        host=args.host,
        port=args.port,
        workers=1 if args.reload else args.workers,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
EOF

# Create __init__.py files for all packages
find app -type d -exec touch {}/__init__.py \;

# Update imports in app.py
echo "Updating imports in app.py..."
sed -i '' 's/from app.utils.config/from app.utils.config_loader/g' app/core/app.py
sed -i '' 's/from app.utils.chart_config/from app.utils.chart.config/g' app/core/app.py
sed -i '' 's/from app.fastapi_dashboard/from app.core.dashboard/g' app/core/app.py

# Update imports in dashboard.py
echo "Updating imports in dashboard.py..."
sed -i '' 's/from app.utils.config/from app.utils.config_loader/g' app/core/dashboard.py
sed -i '' 's/from app.utils.chart_config/from app.utils.chart.config/g' app/core/dashboard.py
sed -i '' 's/from app.utils.interactive_charts/from app.utils.chart.generator/g' app/core/dashboard.py
sed -i '' 's/from app.fastapi_data_access/from app.core.data_access/g' app/core/dashboard.py
sed -i '' 's/from app.utils.sample_data/from app.utils.data_generator/g' app/core/dashboard.py

# Update imports in data_access.py
echo "Updating imports in data_access.py..."
sed -i '' 's/from app.utils.bigquery/from app.utils.db/g' app/core/data_access.py
sed -i '' 's/from app.utils.sample_data/from app.utils.data_generator/g' app/core/data_access.py

# Update imports in chart files
echo "Updating imports in chart files..."
sed -i '' 's/from app.utils.config/from app.utils.config_loader/g' app/utils/chart/config.py

# Create optimized run script
echo "Creating optimized run script..."
cat > run.sh << 'EOF'
#!/bin/bash

# Set environment variables
export PYTHONPATH="$(pwd)"

# Get arguments
PORT=${1:-8080}
WORKERS=${2:-0}  # 0 means auto-detect based on CPU count
RELOAD=0

# Parse options
while [[ $# -gt 0 ]]; do
  case $1 in
    --dev)
      RELOAD=1
      shift
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --workers=*)
      WORKERS="${1#*=}"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# Set up virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for BigQuery credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✓ Using Google Application Credentials from: $GOOGLE_APPLICATION_CREDENTIALS"
else
    echo "⚠ No Google Application Credentials found"
    echo "Using sample data"
fi

# Run the application
if [ $RELOAD -eq 1 ]; then
    echo "Starting in development mode with auto-reload..."
    python -m app --port $PORT --reload
else
    if [ $WORKERS -eq 0 ]; then
        echo "Starting in production mode..."
        python -m app --port $PORT
    else
        echo "Starting in production mode with $WORKERS workers..."
        python -m app --port $PORT --workers $WORKERS
    fi
fi
EOF

chmod +x run.sh

# Create README with new structure
echo "Creating new README..."
cat > README.md << 'EOF'
# FinOps360 Cost Analysis Dashboard

A FastAPI application for visualizing and analyzing cloud costs data.

## Features

- Interactive dashboard for cost analysis
- Asynchronous data processing for better performance
- Support for BigQuery data source
- Interactive charts for data visualization
- Responsive design for all device sizes

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd cost-analysis

# Install dependencies (automatically done when running the app)
pip install -r requirements.txt
```

## Running the Application

```bash
# Production mode
./run.sh [port] [workers]

# Development mode with auto-reload
./run.sh --dev

# Examples:
./run.sh                    # Run on default port 8080
./run.sh 9000               # Run on port 9000
./run.sh --port=9000        # Same as above
./run.sh --workers=2        # Run with 2 workers
./run.sh --dev              # Run in development mode
```

## API Endpoints

- `/` - Main dashboard
- `/loading` - Loading page with auto-redirect
- `/api/health` - Health check endpoint

## Project Structure

```
cost-analysis/
├── app/                    # Main application package
│   ├── core/               # Core application code
│   │   ├── app.py          # FastAPI application
│   │   ├── dashboard.py    # Dashboard generator
│   │   └── data_access.py  # Data access functions
│   ├── utils/              # Utility modules
│   │   ├── chart/          # Chart generation utilities
│   │   │   ├── config.py   # Chart configuration
│   │   │   └── generator.py # Chart generator
│   │   ├── config_loader.py # Configuration loader
│   │   ├── data_generator.py # Sample data generator
│   │   └── db.py           # Database utilities
│   ├── config/             # Configuration files
│   │   ├── config.yaml     # Main configuration
│   │   └── requirements.txt # Dependencies
│   ├── templates/          # HTML templates
│   │   ├── dashboard_template.html
│   │   ├── error.html
│   │   └── loading.html
│   ├── sql/                # SQL queries
│   ├── static/             # Static assets
│   └── __main__.py         # Entry point
├── docs/                   # Documentation
├── requirements.txt        # Symlink to app/config/requirements.txt
├── config.yaml             # Symlink to app/config/config.yaml
└── run.sh                  # Run script
```

## Configuration

Configuration is managed via `app/config/config.yaml`:

```yaml
# BigQuery settings
bigquery:
  project_id: your-project-id
  dataset: your-dataset
  cost_table: your-cost-table
  avg_table: your-avg-table-name

# Chart settings
charts:
  enabled: true

# Data settings
data:
  day_current_date: "2025-05-03"
  day_previous_date: "2025-05-02"
  # ... other settings
  
# Output settings
output:
  directory: reports
```

## License

[Include license information here]
EOF

# Clean up extra files
echo "Cleaning up extra files..."
rm -f run_fastapi.sh run_fastapi_prod.sh quick_test.sh cleanup_legacy.sh

echo "✓ Reorganization complete!"
echo "Run the application with: ./run.sh"