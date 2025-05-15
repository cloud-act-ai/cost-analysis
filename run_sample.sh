#!/bin/bash

# Simplified script for running FinOps360 Cost Analysis with sample data
export PYTHONPATH="$(pwd)"

# Parse options
PORT=8080
RELOAD=0

# Show usage information
if [[ "$1" == "--help" ]]; then
  echo "FinOps360 Cost Analysis Dashboard (Sample Data Mode)"
  echo "------------------------------------------------"
  echo "Usage: ./run_sample.sh [options]"
  echo ""
  echo "Options:"
  echo "  --dev           Run in development mode with auto-reload"
  echo "  --port=PORT     Specify the port to run on (default: 8080)"
  echo ""
  exit 0
fi

# Parse command line arguments
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
    *)
      shift
      ;;
  esac
done

# Clear any existing BigQuery credentials to force sample data mode
unset GOOGLE_APPLICATION_CREDENTIALS

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

# Ensure all dependencies are installed in the virtual environment
echo "Installing/updating dependencies..."
pip install --upgrade -r requirements.txt

# Check if db-dtypes is installed (critical for BigQuery data handling)
if ! pip list | grep -q "db-dtypes"; then
    echo "⚠️ db-dtypes package not found. Installing now..."
    pip install db-dtypes>=1.1.1
fi

echo "🧪 Using SAMPLE DATA mode"

# Run the application
if [ $RELOAD -eq 1 ]; then
    echo "Starting in development mode with auto-reload..."
    python -m app --port $PORT --reload
else
    echo "Starting in production mode..."
    python -m app --port $PORT
fi